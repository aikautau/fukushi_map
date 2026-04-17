var categoryStyles = {
  '居宅支援':       { color: '#4CAF50', label: '居宅' },
  'デイ':           { color: '#FF9800', label: 'デイ' },
  'リハ':           { color: '#2196F3', label: 'リハ' },
  '訪問':           { color: '#9C27B0', label: '訪問' },
  '多機能・密着型': { color: '#F44336', label: '多機' },
  '短期入所':       { color: '#00BCD4', label: '短期' },
  '施設':           { color: '#795548', label: '施設' },
  '用具・住改':     { color: '#607D8B', label: '用具' }
};

var styleCache = {};

function facilityStyleFunction(feature) {
  var cat = feature.get('category');
  if (styleCache[cat]) return styleCache[cat];

  var def = categoryStyles[cat] || { color: '#999', label: '?' };
  styleCache[cat] = new ol.style.Style({
    image: new ol.style.Circle({
      radius: 7,
      fill: new ol.style.Fill({ color: def.color }),
      stroke: new ol.style.Stroke({ color: '#fff', width: 1.5 })
    })
  });
  return styleCache[cat];
}

var selectedArea = null;

function areaPolyStyleFunction(feature) {
  var areaId = feature.get('area_id');
  var isSelected = (selectedArea !== null && selectedArea == areaId);

  if (selectedArea === null) {
    return new ol.style.Style({
      stroke: new ol.style.Stroke({ color: '#1BA466', width: 1.5 }),
      fill: new ol.style.Fill({ color: 'rgba(27, 164, 102, 0.08)' }),
      text: new ol.style.Text({
        text: feature.get('center_name'),
        font: '12px sans-serif',
        fill: new ol.style.Fill({ color: '#1BA466' }),
        stroke: new ol.style.Stroke({ color: '#fff', width: 3 })
      })
    });
  }

  if (isSelected) {
    return new ol.style.Style({
      stroke: new ol.style.Stroke({ color: '#1BA466', width: 3 }),
      fill: new ol.style.Fill({ color: 'rgba(27, 164, 102, 0.25)' }),
      text: new ol.style.Text({
        text: feature.get('center_name'),
        font: 'bold 13px sans-serif',
        fill: new ol.style.Fill({ color: '#0d7a42' }),
        stroke: new ol.style.Stroke({ color: '#fff', width: 3 })
      })
    });
  }

  return new ol.style.Style({
    stroke: new ol.style.Stroke({ color: 'rgba(27, 164, 102, 0.3)', width: 1 }),
    fill: new ol.style.Fill({ color: 'rgba(27, 164, 102, 0.02)' })
  });
}
