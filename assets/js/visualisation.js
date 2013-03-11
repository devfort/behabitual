var map = function(list, callback, context) {
  if (list.map) return list.map(callback, context);
  var result = [];
  for (var i = 0, n = list.length; i < n; i++) {
    result[i] = callback.call(context, list[i], i, list);
  }
  return result;
};


var stepRange = function(begin, end, count) {
  var dx = (end - begin) / count, result = [];
  for (var i = 0; i < count; i++)
    result[i] = begin + i * dx;
  return result;
};


var Point = function(x, y) {
  this.x = x;
  this.y = y;
};

Point.prototype.add = function(point) {
  this.x += point.x;
  this.y += point.y;
  return this;
};

Point.prototype.scale = function(factor) {
  this.x *= factor;
  this.y *= factor;
  return this;
};


var Canvas = function(id, width, height) {
  this._center  = new Point(width/2, height/2);
  this._raph    = Raphael(id, width, height);
  this._objects = [];
};

Canvas.LOGO_PATH   = '/static/images/repeat-icon.svg';
Canvas.LOGO_WIDTH  = 120;
Canvas.LOGO_HEIGHT = 120;

Canvas.prototype.createCircle = function(center, radius) {
  return this._raph.circle(center.x, center.y, radius);
};

Canvas.prototype.createNotch = function(width, height) {
  return this._raph.rect(0, 0, width, height);
};

Canvas.prototype.getCenter = function() {
  return this._center;
};

Canvas.prototype.play = function(params) {
  if (this._timer) return;

  var logo = this._raph.image(Canvas.LOGO_PATH,
                this._center.x - Canvas.LOGO_WIDTH/2,
                this._center.y - Canvas.LOGO_HEIGHT/2,
                Canvas.LOGO_WIDTH, Canvas.LOGO_HEIGHT);

  logo.attr('opacity', 0);
  logo.animate({opacity: 1}, params.easing.duration * 1000);

  this._params = params;
  var time = 0, self = this;

  this._timer = setInterval(function() {
    time += params.tick;
    self.tick(time);
  }, params.tick);
};

Canvas.prototype.register = function(object) {
  this._objects.push(object);
};

Canvas.prototype.tick = function(time) {
  map(this._objects, function(o) { o.tick(time, this._params) }, this);
};


var Easing = {};

Easing.Exponent = function(duration) {
  this.duration = duration;
};
Easing.Exponent.prototype.valueAt = function(time) {
  var x = 5 * time / this.duration;
  return Math.exp(-x);
};

Easing.Reciprocal = function(duration) {
  this.duration = duration;
};
Easing.Reciprocal.prototype.valueAt = function(time) {
  var x = 1 + 19 * time / this.duration;
  return 1 / x;
};


var Orbital = function(size, color, points, frequencies) {
  this._radius = size;
  this._color  = color;
  this._points = points;
  this._freq   = frequencies;
};

Orbital.DOT_RADIUS = 4;

Orbital.prototype.renderOn = function(canvas) {
  this._canvas = canvas;
  canvas.register(this);
  this._circles = map(this._points, function(offset) {
    var circle = canvas.createCircle(canvas.getCenter(), Orbital.DOT_RADIUS);
    circle.attr('fill', this._color);
    circle.attr('stroke-width', 0);
    return circle;
  }, this);
};

Orbital.prototype.tick = function(time, params) {
  map(this._points, function(point, i) {
    var angle  = point * 2 * Math.PI + this._freq[0] * time / 1000,

        orbit  = (  1 + params.to +
                    (params.from - params.to) * params.easing.valueAt(time/1000)
                 ) *
                 this._radius,

        center = new Point(-Math.sin(angle), -Math.cos(angle))
                 .scale(orbit)
                 .add(this._canvas.getCenter());

    this._circles[i].attr('cx', center.x);
    this._circles[i].attr('cy', center.y);
  }, this);
};


var Ring = function(size, color, filled, frequencies) {
  this._radius = size;
  this._color  = color;
  this._filled = filled;
  this._freq   = frequencies;
};

Ring.MARKER_WIDTH  = 2;
Ring.MARKER_HEIGHT = 8;
Ring.NUM_NOTCHES   = 3;
Ring.NOTCH_OPACITY = 0.4;
Ring.NOTCH_COLOR   = '#ffffff';

Ring.prototype.renderOn = function(canvas) {
  this._canvas = canvas;
  canvas.register(this);
  this._circle = canvas.createCircle(canvas.getCenter(), this._radius);

  if (this._filled) {
    this._circle.attr('fill', this._color);
    this._circle.attr('stroke-width', 0);

    this._notches = map(stepRange(0, 1, Ring.NUM_NOTCHES), function(offset) {
      var notch = this._canvas.createNotch(Ring.MARKER_WIDTH, Ring.MARKER_HEIGHT);
      notch.attr({'fill': Ring.NOTCH_COLOR, 'stroke-width': 0, 'opacity': Ring.NOTCH_OPACITY});
      return notch;
    }, this);
  }
  else {
    this._circle.attr('stroke', this._color);
    this._circle.attr('stroke-width', this._radius / 20);
  }
};

Ring.prototype.tick = function(time, params) {
  var angle  = this._freq[0] * time / 1000,

      orbit  = (  params.to +
                  (params.from - params.to) * params.easing.valueAt(time/1000)
               ) *
               this._radius,

      center = new Point(Math.sin(angle), -Math.cos(angle))
               .scale(orbit)
               .add(this._canvas.getCenter());

  this._circle.attr('cx', center.x);
  this._circle.attr('cy', center.y);

  if (!this._notches) return;

  map(this._notches, function(notch, i) {
    var theta = 2 * Math.PI * i * 1/Ring.NUM_NOTCHES +
                (angle * (orbit + this._radius)) / (2 * Math.PI * this._radius);

    var N = new Point(-Math.sin(theta), -Math.cos(theta))
                .scale(this._radius - Ring.MARKER_HEIGHT/2)
                .add(center);

    notch.attr('x', N.x - Ring.MARKER_WIDTH/2);
    notch.attr('y', N.y - Ring.MARKER_HEIGHT/2);
    notch.attr('rotation', -theta * 180/Math.PI);
  }, this);
};


(function() {
  var objects = [
    new Ring(140, '#d4d8d2', true,  [6]),
    new Ring(110, '#4389b8', false, [2]),
    new Ring(100, '#4389b8', true,  [4]),
    new Orbital(150, '#f94630', [0.01, 0.02, 0.04, 0.08, 0.16], [1.5]),
    new Orbital(170, '#4389b8', [1.04, 1.08, 1.16], [1.2])
  ];

  var canvas = new Canvas('visualisation', 480, 480);
  map(objects, function(r) { r.renderOn(canvas) });
  canvas.play({from: 1, to: 0.05, tick: 20, easing: new Easing.Exponent(4)});
})();

