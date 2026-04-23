(function() {
  var hmap = new Hukushimap();
  hmap.generate([135.673, 34.814], 13);

  var map = hmap.map;
  var popupEl = document.getElementById('popup');
  var popupTitle = document.getElementById('popup-title');
  var popupContent = document.getElementById('popup-content');
  var popupCloser = document.getElementById('popup-closer');

  popupCloser.addEventListener('click', function(e) {
    e.preventDefault();
    hmap.popup.setPosition(undefined);
    popupEl.style.display = 'none';
  });

  var categoryToLayer = {
    '居宅支援':       'layerKyotaku',
    'デイ':           'layerDay',
    'リハ':           'layerRiha',
    '訪問':           'layerHoumon',
    '多機能・密着型': 'layerTakinou',
    '短期入所':       'layerTanki',
    '施設':           'layerShisetsu',
    '用具・住改':     'layerYougu'
  };

  var cbToLayer = {
    'cbKyotaku':  'layerKyotaku',
    'cbDay':      'layerDay',
    'cbRiha':     'layerRiha',
    'cbHoumon':   'layerHoumon',
    'cbTakinou':  'layerTakinou',
    'cbTanki':    'layerTanki',
    'cbShisetsu': 'layerShisetsu',
    'cbYougu':    'layerYougu'
  };

  // Load facility GeoJSON + geocoding dictionaries, then init FacilitySearch
  var allFeatures = [];
  var search = null;

  function fetchJson(url) {
    return fetch(url).then(function(r) { return r.json(); });
  }

  // 辞書の _ 始まりメタキーを除去
  function stripMeta(obj) {
    var out = {};
    for (var k in obj) {
      if (obj.hasOwnProperty(k) && k.charAt(0) !== '_') out[k] = obj[k];
    }
    return out;
  }

  Promise.all([
    fetchJson('data/jigyosho.geojson'),
    fetchJson('data/geocoding_gaiku.json'),
    fetchJson('data/geocoding_oaza.json'),
    fetchJson('data/geocoding_towns.json')
  ]).then(function(results) {
    var geojson = results[0];
    var gaiku = stripMeta(results[1]);
    var oaza = stripMeta(results[2]);
    var towns = results[3];

    var format = new ol.format.GeoJSON();
    allFeatures = format.readFeatures(geojson, {
      featureProjection: 'EPSG:3857'
    });

    var buckets = {};
    allFeatures.forEach(function(f) {
      var cat = f.get('category');
      var layerName = categoryToLayer[cat];
      if (!layerName) return;
      if (!buckets[layerName]) buckets[layerName] = [];
      buckets[layerName].push(f);
    });
    Object.keys(buckets).forEach(function(name) {
      hmap.addFacilityLayer(name, buckets[name]);
    });

    search = new FacilitySearch(hmap, allFeatures, gaiku, oaza, towns);
    search.attach(
      document.getElementById('searchBox'),
      document.getElementById('searchSuggest')
    );
    if (centerFeaturesPending) {
      search.setCenters(centerFeaturesPending);
      centerFeaturesPending = null;
    }
  });

  // Load area polygons
  fetch('data/chiiki_houkatsu.geojson')
    .then(function(r) { return r.json(); })
    .then(function(geojson) {
      var format = new ol.format.GeoJSON();
      var features = format.readFeatures(geojson, {
        featureProjection: 'EPSG:3857'
      });
      hmap.addAreaLayer(features);

      var select = document.getElementById('selectArea');
      features.sort(function(a, b) { return a.get('area_id') - b.get('area_id'); });
      features.forEach(function(f) {
        var opt = document.createElement('option');
        opt.value = f.get('area_id');
        opt.textContent = '第' + f.get('area_id') + ' ' + f.get('center_name');
        select.appendChild(opt);
      });
    });

  // Load houkatsu center points
  var centerFeaturesPending = null;
  fetch('data/houkatsu_centers.geojson')
    .then(function(r) { return r.json(); })
    .then(function(geojson) {
      var format = new ol.format.GeoJSON();
      var features = format.readFeatures(geojson, {
        featureProjection: 'EPSG:3857'
      });
      hmap.addCenterLayer(features);
      if (search) {
        search.setCenters(features);
      } else {
        centerFeaturesPending = features;
      }
    });

  // Category checkbox handlers
  Object.keys(cbToLayer).forEach(function(cbId) {
    var cb = document.getElementById(cbId);
    if (!cb) return;
    cb.addEventListener('change', function() {
      hmap.setLayerVisible(cbToLayer[cbId], cb.checked);
    });
  });

  // Area polygon toggle
  document.getElementById('cbArea').addEventListener('change', function() {
    hmap.setLayerVisible('areaLayer', this.checked);
  });

  // Houkatsu center toggle
  document.getElementById('cbCenter').addEventListener('change', function() {
    hmap.setLayerVisible('centerLayer', this.checked);
  });

  // Area dropdown
  document.getElementById('selectArea').addEventListener('change', function() {
    var val = this.value;
    if (val === '') {
      selectedArea = null;
    } else {
      selectedArea = parseInt(val);
      hmap.zoomToArea(selectedArea);
    }
    hmap.refreshAreaStyle();
  });

  // Click → popup
  map.on('singleclick', function(evt) {
    var hit = false;
    map.forEachFeatureAtPixel(evt.pixel, function(feature, layer) {
      if (hit) return;
      var geomType = feature.getGeometry().getType();
      if (geomType === 'Point') {
        popupTitle.innerHTML = hmap.getPopupTitle(feature);
        popupContent.innerHTML = hmap.getPopupContent(feature);
        hmap.popup.setPosition(feature.getGeometry().getCoordinates());
        popupEl.style.display = 'block';
        hit = true;
      }
    });
    if (!hit) {
      hmap.popup.setPosition(undefined);
      popupEl.style.display = 'none';
    }
  });

  // Pointer cursor on facility hover
  map.on('pointermove', function(evt) {
    var pixel = map.getEventPixel(evt.originalEvent);
    var hasFeature = false;
    map.forEachFeatureAtPixel(pixel, function(feature) {
      if (feature.getGeometry().getType() === 'Point') hasFeature = true;
    });
    map.getTargetElement().style.cursor = hasFeature ? 'pointer' : '';
  });
})();
