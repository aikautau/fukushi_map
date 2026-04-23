// 事業所名検索＋住所ジオコーディング
// 既存の Hukushimap / ol_style.js / hukushimap.js と同じ prototype + ES5 スタイル。

function FacilitySearch(hmap, facilities, gaiku, oaza, towns) {
  this.hmap = hmap;
  this.map = hmap.map;
  this.facilities = facilities;       // ol.Feature[]（全事業所）
  this.gaiku = gaiku;                 // { "町名\t街区符号": [lon,lat] }
  this.oaza = oaza;                   // { "町名": [lon,lat] }
  this.towns = towns;                 // 町名配列（長さ降順）
  this.inputEl = null;
  this.suggestEl = null;
  this._debounceTimer = null;
  this._pinLayer = null;
  this._pinFeature = null;
  this._buildPinLayer();
}

FacilitySearch.prototype._buildPinLayer = function() {
  this._pinLayer = new ol.layer.Vector({
    source: new ol.source.Vector(),
    style: new ol.style.Style({
      image: new ol.style.Circle({
        radius: 10,
        fill: new ol.style.Fill({ color: 'rgba(229,57,53,0.25)' }),
        stroke: new ol.style.Stroke({ color: '#E53935', width: 3 })
      })
    }),
    name: 'searchPinLayer',
    zIndex: 30
  });
  this.map.addLayer(this._pinLayer);
};

FacilitySearch.prototype.attach = function(inputEl, suggestEl) {
  this.inputEl = inputEl;
  this.suggestEl = suggestEl;
  var self = this;

  inputEl.addEventListener('input', function() {
    var q = inputEl.value;
    if (self._debounceTimer) clearTimeout(self._debounceTimer);
    self._debounceTimer = setTimeout(function() { self._onInput(q); }, 150);
  });

  inputEl.addEventListener('focus', function() {
    if (suggestEl.children.length > 0) suggestEl.style.display = 'block';
  });

  // 外側クリックでサジェストを閉じる
  document.addEventListener('click', function(e) {
    if (e.target !== inputEl && !suggestEl.contains(e.target)) {
      suggestEl.style.display = 'none';
    }
  });
};

// ── 入力正規化 ─────────────────────────────
FacilitySearch.prototype._normalizeInput = function(s) {
  if (!s) return '';
  // 全角数字 → 半角
  s = s.replace(/[０-９]/g, function(c) {
    return String.fromCharCode(c.charCodeAt(0) - 0xFEE0);
  });
  // ハイフン類 → -
  s = s.replace(/[－ー−‐—–]/g, '-');
  // ヶ/ｹ/が → ケ（住所の文脈）
  s = s.replace(/[ヶｹ]/g, 'ケ').replace(/が/g, 'ケ');
  // 接頭辞 「大阪府枚方市」「枚方市」を除去
  s = s.replace(/^大阪府?枚方市/, '').replace(/^枚方市/, '');
  // 「N丁X」→「N丁目X」 補正
  s = s.replace(/(\d+)丁(\d)/g, '$1丁目$2');
  // 表記ゆれを片側に揃える（辞書は両方のバリアントで登録済み。
  // 入力と施設名の両方で同じ正規化を行うことで、"楠葉"で"樟葉〇〇"もヒットする）
  s = s.replace(/樟葉/g, '楠葉');
  s = s.replace(/招堤/g, '招提');
  return s.trim();
};

// ── 施設名マッチ ─────────────────────────────
FacilitySearch.prototype._searchFacilities = function(q) {
  if (!q) return [];
  var nq = this._normalizeInput(q).toLowerCase();
  if (!nq) return [];
  var results = [];
  for (var i = 0; i < this.facilities.length && results.length < 8; i++) {
    var f = this.facilities[i];
    var name = (f.get('name') || '');
    var nname = this._normalizeInput(name).toLowerCase();
    if (nname.indexOf(nq) >= 0) {
      results.push(f);
    }
  }
  return results;
};

// ── ジオコーディング（scripts/geocode.py の簡易版） ─────
FacilitySearch.prototype._extractBlock = function(s) {
  if (!s) return '';
  s = s.replace(/^[番地のノ-]+/, '');
  var m = s.match(/^(\d+)/);
  return m ? m[1] : '';
};

FacilitySearch.prototype._matchTown = function(addr) {
  // 最長一致（towns は長さ降順）で addr の先頭に一致する町名を返す
  for (var i = 0; i < this.towns.length; i++) {
    var t = this.towns[i];
    if (t && addr.indexOf(t) === 0) return t;
  }
  return '';
};

FacilitySearch.prototype._geocode = function(q) {
  var addr = this._normalizeInput(q);
  if (!addr) return null;

  // 1) 町名（丁目込み）で最長一致
  var town = this._matchTown(addr);
  if (town) {
    var rest = addr.substring(town.length);
    var block = this._extractBlock(rest);
    if (block) {
      var key = town + '\t' + block;
      if (this.gaiku.hasOwnProperty(key)) {
        return { lonlat: this.gaiku[key], level: 'gaiku', town: town, block: block };
      }
    }
    if (this.oaza.hasOwnProperty(town)) {
      return { lonlat: this.oaza[town], level: 'oaza', town: town };
    }
    // 丁目付き町名の基底部分で大字マッチ
    var base = town.replace(/[一二三四五六七八九十]+丁目$/, '').replace(/\d+丁目$/, '');
    if (base !== town && this.oaza.hasOwnProperty(base)) {
      return { lonlat: this.oaza[base], level: 'oaza_base', town: base };
    }
  }

  // 2) 丁目省略ケース: 最初の数字を丁目として再試行
  //    例: 津田元町1-1-1 → 津田元町1丁目 + block=1
  //    例: 星丘4-33     → 星丘4丁目 + block=33
  var m = addr.match(/^([^\d]+?)(\d+)[-番の]+(\d+)/);
  if (m) {
    var basePart = m[1];
    var first = m[2];
    var second = m[3];
    var candidate = basePart + first + '丁目';
    var ck = candidate + '\t' + second;
    if (this.gaiku.hasOwnProperty(ck)) {
      return { lonlat: this.gaiku[ck], level: 'gaiku', town: candidate, block: second };
    }
    if (this.oaza.hasOwnProperty(candidate)) {
      return { lonlat: this.oaza[candidate], level: 'oaza', town: candidate };
    }
  }

  return null;
};

// ── 入力イベント ─────────────────────────────
FacilitySearch.prototype._onInput = function(query) {
  var q = (query || '').trim();
  if (!q) {
    this.suggestEl.innerHTML = '';
    this.suggestEl.style.display = 'none';
    return;
  }

  var facItems = this._searchFacilities(q);
  var addrItem = this._geocode(q);
  this._renderSuggest(q, facItems, addrItem);
};

// ── サジェスト描画 ─────────────────────────────
FacilitySearch.prototype._renderSuggest = function(query, facItems, addrItem) {
  var self = this;
  var sug = this.suggestEl;
  sug.innerHTML = '';

  if (facItems.length === 0 && !addrItem) {
    var miss = document.createElement('div');
    miss.className = 'list-group-item text-muted';
    miss.textContent = '該当する施設・住所が見つかりません';
    sug.appendChild(miss);
    sug.style.display = 'block';
    return;
  }

  if (addrItem) {
    var levelLabel = addrItem.level === 'gaiku' ? '街区'
      : addrItem.level === 'oaza' ? '大字' : '大字基底';
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'list-group-item list-group-item-action';
    btn.innerHTML = '<span class="badge bg-info">住所</span> ' +
      '<span class="ms-1">' + escHtml(addrItem.town + (addrItem.block ? addrItem.block : '')) + '</span>' +
      '<small class="text-muted d-block">' + levelLabel + 'レベルで一致</small>';
    btn.addEventListener('click', function() {
      self._pickAddress(query, addrItem);
      sug.style.display = 'none';
    });
    sug.appendChild(btn);
  }

  for (var i = 0; i < facItems.length; i++) {
    (function(f) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'list-group-item list-group-item-action';
      var name = f.get('name') || '';
      var addr = f.get('address_full') || '';
      var cat = f.get('category') || '';
      btn.innerHTML = '<span class="badge bg-secondary">施設</span> ' +
        '<span class="ms-1">' + escHtml(name) + '</span>' +
        '<small class="text-muted d-block">' + escHtml(cat) + '｜' + escHtml(addr) + '</small>';
      btn.addEventListener('click', function() {
        self._pickFacility(f);
        sug.style.display = 'none';
      });
      sug.appendChild(btn);
    })(facItems[i]);
  }

  sug.style.display = 'block';
};

// ── 施設を選択：ズーム＋既存popup ─────────────
FacilitySearch.prototype._pickFacility = function(feature) {
  this._clearPin();
  var coord = feature.getGeometry().getCoordinates();
  this.map.getView().animate({ center: coord, zoom: 17, duration: 400 });

  var popupEl = document.getElementById('popup');
  var popupTitle = document.getElementById('popup-title');
  var popupContent = document.getElementById('popup-content');
  popupTitle.innerHTML = this.hmap.getPopupTitle(feature);
  popupContent.innerHTML = this.hmap.getPopupContent(feature);
  this.hmap.popup.setPosition(coord);
  popupEl.style.display = 'block';
};

// ── 住所を選択：ピン＋popup ─────────────────
FacilitySearch.prototype._pickAddress = function(query, result) {
  this._clearPin();
  var lonlat = result.lonlat;
  var coord = ol.proj.fromLonLat(lonlat);
  this.map.getView().animate({ center: coord, zoom: 17, duration: 400 });

  var feat = new ol.Feature({ geometry: new ol.geom.Point(coord) });
  this._pinFeature = feat;
  this._pinLayer.getSource().addFeature(feat);

  var levelLabel = result.level === 'gaiku' ? '街区レベル'
    : result.level === 'oaza' ? '大字レベル' : '大字基底レベル';

  var popupEl = document.getElementById('popup');
  var popupTitle = document.getElementById('popup-title');
  var popupContent = document.getElementById('popup-content');
  popupTitle.innerHTML = '<i class="bi bi-geo-alt-fill" style="color:#E53935"></i> <strong>検索した住所</strong>';
  popupContent.innerHTML = '<table>' +
    '<tr><th>入力</th><td>' + escHtml(query) + '</td></tr>' +
    '<tr><th>一致</th><td>' + escHtml(result.town + (result.block ? result.block : '')) + '</td></tr>' +
    '<tr><th>精度</th><td>' + levelLabel + '</td></tr>' +
    '</table>';
  this.hmap.popup.setPosition(coord);
  popupEl.style.display = 'block';
};

FacilitySearch.prototype._clearPin = function() {
  if (this._pinFeature) {
    this._pinLayer.getSource().removeFeature(this._pinFeature);
    this._pinFeature = null;
  }
};
