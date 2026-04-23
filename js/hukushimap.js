function Hukushimap() {
  this.map = null;
  this.facilityLayers = {};
  this.areaLayer = null;
  this.centerLayer = null;
  this.popup = null;
}

Hukushimap.prototype.generate = function(center, zoom) {
  var tileLayer = new ol.layer.Tile({
    source: new ol.source.XYZ({
      url: 'https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',
      attributions: '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank">国土地理院</a>'
    }),
    name: 'basemap'
  });

  var popupEl = document.getElementById('popup');
  this.popup = new ol.Overlay({
    element: popupEl,
    autoPan: { animation: { duration: 250 } }
  });

  this.map = new ol.Map({
    target: 'map',
    layers: [tileLayer],
    overlays: [this.popup],
    view: new ol.View({
      center: ol.proj.fromLonLat(center),
      zoom: zoom,
      minZoom: 10,
      maxZoom: 18
    }),
    controls: ol.control.defaults.defaults().extend([
      new ol.control.ScaleLine()
    ])
  });
};

Hukushimap.prototype.addFacilityLayer = function(name, features) {
  var layer = new ol.layer.Vector({
    source: new ol.source.Vector({ features: features }),
    style: facilityStyleFunction,
    name: name,
    zIndex: 20
  });
  this.facilityLayers[name] = layer;
  this.map.addLayer(layer);
};

Hukushimap.prototype.addAreaLayer = function(features) {
  this.areaLayer = new ol.layer.Vector({
    source: new ol.source.Vector({ features: features }),
    style: areaPolyStyleFunction,
    name: 'areaLayer',
    zIndex: 5
  });
  this.map.addLayer(this.areaLayer);
};

Hukushimap.prototype.addCenterLayer = function(features) {
  this.centerLayer = new ol.layer.Vector({
    source: new ol.source.Vector({ features: features }),
    style: houkatsuCenterStyleFunction,
    name: 'centerLayer',
    zIndex: 30
  });
  this.map.addLayer(this.centerLayer);
};

Hukushimap.prototype.setLayerVisible = function(name, visible) {
  var layers = this.map.getLayers();
  layers.forEach(function(layer) {
    if (layer.get('name') === name) {
      layer.setVisible(visible);
    }
  });
};

Hukushimap.prototype.refreshAreaStyle = function() {
  if (this.areaLayer) {
    this.areaLayer.getSource().changed();
  }
};

Hukushimap.prototype.zoomToArea = function(areaId) {
  if (!this.areaLayer) return;
  var features = this.areaLayer.getSource().getFeatures();
  for (var i = 0; i < features.length; i++) {
    if (features[i].get('area_id') == areaId) {
      var geom = features[i].getGeometry();
      this.map.getView().fit(geom, { padding: [60, 60, 60, 60], duration: 500 });
      return;
    }
  }
};

function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

Hukushimap.prototype.getPopupTitle = function(feature) {
  if (feature.get('area_id') && feature.get('center_name')) {
    var cname = feature.get('center_name');
    return '<span style="color:#0d7a42">\u25cf</span> ' +
           '<strong>\u7b2c' + feature.get('area_id') + '\u570f\u57df ' + escHtml(cname) + '</strong>';
  }
  var cat = feature.get('category') || '';
  var name = feature.get('name') || '';
  var def = categoryStyles[cat] || { color: '#999' };
  return '<span style="color:' + def.color + '">\u25cf</span> ' +
         '<strong>' + escHtml(name) + '</strong>';
};

Hukushimap.prototype.getPopupContent = function(feature) {
  var rows = [];
  function addRow(label, val) {
    if (val && val !== '0' && val !== '') {
      rows.push('<tr><th>' + escHtml(label) + '</th><td>' + escHtml(val) + '</td></tr>');
    }
  }

  if (feature.get('area_id') && feature.get('center_name')) {
    addRow('種別', '地域包括支援センター');
    addRow('担当校区', feature.get('school_districts'));
    addRow('住所', feature.get('address_full'));
    if (feature.get('tel')) {
      var telC = feature.get('tel');
      rows.push('<tr><th>電話</th><td><a href="tel:' + escHtml(telC) + '">' + escHtml(telC) + '</a></td></tr>');
    }
    return '<table>' + rows.join('') + '</table>';
  }

  addRow('種別', feature.get('category'));
  addRow('サービス', feature.get('service_type'));
  addRow('住所', feature.get('address_full'));
  if (feature.get('tel')) {
    var tel = feature.get('tel');
    rows.push('<tr><th>電話</th><td><a href="tel:' + escHtml(tel) + '">' + escHtml(tel) + '</a></td></tr>');
  }
  addRow('定員', feature.get('capacity'));
  return '<table>' + rows.join('') + '</table>';
};
