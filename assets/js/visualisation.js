/**
 * Visualisation module
 * ====================
 *
 * Listen, alright, shut up, just listen. This will make sense eventually, though
 * I'm not convinced the rest of the week will. I took George's demo and turned
 * it into a bunch of drawing objects that you can use to make visualisations
 * easily (read: rewrote 30 lines of JS in 200 lines because webscale). By the
 * way George is one of the most helpful and generous humans I know, you should
 * definitely buy him an drink.
 *
 * Oh and plus also Chris brought me and George some whisky while we were up on
 * the roof of the officer's mess, trying to use a computer. That was pretty much
 * the nicest thing anyone ever did for me. In these tumultuous times, with the
 * wind lashing across the island and the causeway submerged by vengeful seas, it
 * is these memories that give us all hope.
 *
 * You find our intrepid explorers facing potential perpetual entombment on the
 * island of Alderney. Faceplanes having been deemed unable to face the howling
 * gales of March 2013, which were said to have left Beaufort himself rotating at
 * a steady clip in his watery grave, the survivors of /dev/fort 7 take shelter
 * in the kitchen of Fort Clonque, surviving as best they can on half a bottle of
 * Scotch and some ham of questionable provenance.
 *
 * It is Monday morning. Send halp.
 *
 * Anyway, where were we. Right, JavaScripts. This module will help you visualize
 * a person's habits, such as they are.
 *
 * You make a visualization by making some drawing objects, and rendering them to
 * a canvas. There are two types of drawing objects: Rings and Orbitals.
 *
 * A Ring represents a circle that rotates about the center of the canvas. You
 * instantiate it with a radius, color, a boolean that says whether it should be
 * filled or not, and a list containing rotation frequency parameters.
 *
 *    var ring = new Ring(140, '#4389b8', true, [4]);
 *
 * An Orbital represents a string of dots that orbit the center of the canvas.
 * They are instantiated with an orbit radius, a color, a list of values between
 * 0 and 1 that denote the positions of dots around the orbit ring, and a list of
 * orbit frequencies.
 *
 *    var orbital = new Orbital(160, '#f9c32c', [0, 0.2, 0.4], [1]);
 *
 * Once you've made a bunch of drawing objects, you render them to a canvas, and
 * then you tell the canvas to play itself, which means run the animation with
 * some defined parameters.
 *
 *    var objects = [ring, orbital, ...];
 *    var canvas  = new Canvas('visualisation', 480, 480);
 *    objects.forEach(function(o) { o.renderOn(canvas) });
 *    canvas.play({from: 1, to: 0.05, tick: 20, easing: new Easing.Exponent(4)});
 *
 * Here are the options for canvas.play():
 *
 *    * `from`: the maximum orbital reach, on the range 0-1
 *    * `to`: the minimum orbital reach, from 0-1
 *    * `tick`: the frequency of the `setInterval()` for the animation loop
 *    * `easing`: an Easing object that determines the progression of `from` to `to` 
 *
 * During start-up, the animation transitions from the `from` to the `to` orbital
 * reach. Converging on `to=0` means reaching maximal concentricity. Values above
 * 0 result in some excentricity of the animation in the steady state.
 *
 * This is all you should need to know. It is implicit in the above documentation
 * and the below code that #loljs, because of <%= reasons %>.
 *
 * While trapped on this island we have learned many things. We can slice onions
 * without crying. I learned some Python. Children will skip rope on the verge of
 * a 50ft cliff. You should aim for the elbow. There is still room for blue-sky
 * innovation in the space around 'Call Me Maybe' parodies. Alas, it is our fear
 * that such knowledge will never reach the mainland.
 *
 * I don't think we're leaving today. We wish you well.
 *
 *
 * Addendum
 * --------
 *
 * In the hopes that our struggles have not been in vain, we include herewith the
 * Proceedings of Cohort 7.
 *
 *  1. Space Jesus. Am I right?
 *  2. Wheee... I'm programming!
 *  3. It was tough, Norm, but I had to Mazz up.
 *  4. GMT or GTFO.
 *  5. Just a word of advice: bellend sounds much funnier than cockend.
 *  6. James will type, I will direct, Anna will make dirty Unix jokes.
 *  7. Since we don't have any cat gifs right now, YAGNI.
 *  8. You've got Stockholm Syndrome from working with Rails.
 *  9. You've got Stockholm Syndrome from living in Stockholm.
 * 10. That's going in the fucking book. The Book of Rueing.
 * 11. Fucking dynamic toothbrusth motherfucker! We're gonna brush that shit up!
 * 12. There's some crazy ass pink shit going on.
 * 13. Shit is gonna get real. It's gonna get really really real.
 * 14. Your face is not a TTY.
 * 15. Romance is a sales problem.
 * 16. I'm running out of fingers to flip you guys off with.
 * 17. You finally worked it out, Nobbo.
 * 18. Just fucking drink the whisky or I'll throw it at a dolphin.
 * 19. We're never getting off this rock, are we?
 * 20. Fuck you!
 *
 * Felicitations. You look nice today. Supertrain will be along presently.
 **/


var filter = function(list, callback, context) {
  if (list.filter) return list.filter(callback, context);
  var result = [];
  for (var i = 0, n = list.length; i < n; i++) {
    if (callback.call(context, list[i], i, list))
      result.push(list[i]);
  }
  return result;
};


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

