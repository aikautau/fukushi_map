var categoryStyles = {
  // 介護（丸形）
  '居宅支援':       { color: '#4CAF50', label: '居宅', shape: 'circle' },
  'デイ':           { color: '#FF9800', label: 'デイ', shape: 'circle' },
  'リハ':           { color: '#2196F3', label: 'リハ', shape: 'circle' },
  '訪問':           { color: '#9C27B0', label: '訪問', shape: 'circle' },
  '多機能・密着型': { color: '#F44336', label: '多機', shape: 'circle' },
  '短期入所':       { color: '#00BCD4', label: '短期', shape: 'circle' },
  '施設':           { color: '#795548', label: '施設', shape: 'circle' },
  '用具・住改':     { color: '#607D8B', label: '用具', shape: 'circle' },
  // 医療（RegularShape で介護と視覚的に区別。色覚多様性を考慮し色だけに頼らない）
  'med_hospital':   { color: '#B71C1C', label: '病院', shape: 'cross' },     // 濃赤・十字
  'med_clinic':     { color: '#E53935', label: '医院', shape: 'square' },    // 赤・四角
  'med_dental':     { color: '#EC407A', label: '歯科', shape: 'diamond' }    // ピンク・菱形
};

var styleCache = {};

function _medicalShape(kind, color) {
  // 介護の Circle とサイズ感を揃えつつ、形状差で医療を識別できるようにする
  if (kind === 'cross') {
    return new ol.style.RegularShape({
      points: 4,
      radius: 8,
      radius2: 0,
      angle: 0,
      stroke: new ol.style.Stroke({ color: color, width: 3 })
    });
  }
  if (kind === 'diamond') {
    return new ol.style.RegularShape({
      points: 4,
      radius: 8,
      angle: Math.PI / 4,
      fill: new ol.style.Fill({ color: color }),
      stroke: new ol.style.Stroke({ color: '#fff', width: 1.5 })
    });
  }
  // square
  return new ol.style.RegularShape({
    points: 4,
    radius: 7,
    angle: Math.PI / 4,
    fill: new ol.style.Fill({ color: color }),
    stroke: new ol.style.Stroke({ color: '#fff', width: 1.5 })
  });
}

function facilityStyleFunction(feature) {
  var cat = feature.get('category');
  if (styleCache[cat]) return styleCache[cat];

  var def = categoryStyles[cat] || { color: '#999', label: '?', shape: 'circle' };
  var image;
  if (def.shape && def.shape !== 'circle') {
    image = _medicalShape(def.shape, def.color);
  } else {
    image = new ol.style.Circle({
      radius: 7,
      fill: new ol.style.Fill({ color: def.color }),
      stroke: new ol.style.Stroke({ color: '#fff', width: 1.5 })
    });
  }
  styleCache[cat] = new ol.style.Style({ image: image });
  return styleCache[cat];
}

var selectedArea = null;

var _centerPinStyle = new ol.style.Style({
  image: new ol.style.Circle({
    radius: 9,
    fill: new ol.style.Fill({ color: '#0d7a42' }),
    stroke: new ol.style.Stroke({ color: '#fff', width: 2.5 })
  }),
  text: new ol.style.Text({
    text: '包',
    font: 'bold 11px sans-serif',
    fill: new ol.style.Fill({ color: '#fff' })
  })
});

function houkatsuCenterStyleFunction(feature) {
  var labelStyle = new ol.style.Style({
    text: new ol.style.Text({
      text: feature.get('center_name') || '',
      font: 'bold 12px sans-serif',
      offsetY: 18,
      fill: new ol.style.Fill({ color: '#0d7a42' }),
      stroke: new ol.style.Stroke({ color: '#fff', width: 3 })
    })
  });
  return [_centerPinStyle, labelStyle];
}

function areaPolyStyleFunction(feature) {
  var areaId = feature.get('area_id');
  var isSelected = (selectedArea !== null && selectedArea == areaId);

  if (selectedArea === null) {
    return new ol.style.Style({
      stroke: new ol.style.Stroke({ color: '#1BA466', width: 1.5 }),
      fill: new ol.style.Fill({ color: 'rgba(27, 164, 102, 0.08)' })
    });
  }

  if (isSelected) {
    return new ol.style.Style({
      stroke: new ol.style.Stroke({ color: '#1BA466', width: 3 }),
      fill: new ol.style.Fill({ color: 'rgba(27, 164, 102, 0.25)' })
    });
  }

  return new ol.style.Style({
    stroke: new ol.style.Stroke({ color: 'rgba(27, 164, 102, 0.3)', width: 1 }),
    fill: new ol.style.Fill({ color: 'rgba(27, 164, 102, 0.02)' })
  });
}
