(function () {
    var canvas, circles = [], markers = [],
        center_x = 320,
        center_y = 240;

    canvas = Raphael('visualisation', 640, 480);

    circles[0] = canvas.circle(center_x, center_y, 130).attr({
        'fill': '#d4d8d2',
        'stroke-width': 0
    });
    circles[1] = canvas.circle(center_x, center_y, 60).attr({
        'stroke': '#4389b8',
        'stroke-width': 3
    });
    circles[2] = canvas.circle(center_x, center_y, 50).attr({
        'fill': '#4389b8',
        'stroke-width': 0
    });

    markers[0] = canvas.rect(318.5, 365, 3, 5).attr({
        'fill': '#fff',
        'stroke-width': 0
    });
    markers[2] = canvas.rect(318.5, 190, 3, 5).attr({
        'fill': '#d4d8d2',
        'stroke-width': 0
    });

    canvas.image('/static/images/repeat-icon.svg', 260, 180, 120, 120);

    var target = 5, x = 0;

    setInterval(function () {
        var instability = target + 10000 / x,
            angle = 0.025 * x,
            angle3 = 0.05 * x;

        // Circle#rotate(angle, center_x, center_y)
        circles[0].rotate(angle, center_x + instability, center_y + instability);
        markers[0].rotate(angle, center_x + instability, center_y + instability);

        circles[1].rotate(angle, center_x - instability, center_y - instability);

        circles[2].rotate(angle3, center_x + instability, center_y - instability);
        markers[2].rotate(angle3, center_x + instability, center_y - instability);

        x += 10;
    }, 10);
})();

