(function () {
    document.querySelectorAll('.bjj-belt__tip[data-max]').forEach(function (tip) {
        if (tip.children.length > 0) return;
        var max = parseInt(tip.dataset.max, 10) || 0;
        var grade = parseInt(tip.dataset.grade, 10) || 0;
        for (var i = 0; i < max; i++) {
            var span = document.createElement('span');
            span.className = 'bjj-belt__stripe' + (i < grade ? ' bjj-belt__stripe--filled' : '');
            tip.appendChild(span);
        }
    });
}());
