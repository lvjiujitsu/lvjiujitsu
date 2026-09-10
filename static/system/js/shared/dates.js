(function () {
  'use strict';

  window.APP = window.APP || {};

  function isoToPtBr(value) {
    if (!value) return '';
    var parts = String(value).split('T')[0].split('-');
    if (parts.length !== 3) return String(value);
    return parts[2] + '/' + parts[1] + '/' + parts[0];
  }

  function pad(value) {
    return value < 10 ? '0' + value : String(value);
  }

  function parseParts(value) {
    if (!value) return null;
    var text = String(value).trim();
    var year;
    var month;
    var day;
    if (text.indexOf('-') !== -1) {
      var isoParts = text.split('T')[0].split('-');
      if (isoParts.length !== 3) return null;
      year = parseInt(isoParts[0], 10);
      month = parseInt(isoParts[1], 10);
      day = parseInt(isoParts[2], 10);
    } else {
      var brParts = text.split('/');
      if (brParts.length !== 3) return null;
      day = parseInt(brParts[0], 10);
      month = parseInt(brParts[1], 10);
      year = parseInt(brParts[2], 10);
    }
    if (!year || !month || !day) return null;
    return { year: year, month: month, day: day };
  }

  function ptBrToIso(value) {
    var parts = parseParts(value);
    if (!parts) return '';
    return parts.year + '-' + pad(parts.month) + '-' + pad(parts.day);
  }

  function ageYears(value) {
    var parts = parseParts(value);
    if (!parts) return null;
    var born = new Date(parts.year, parts.month - 1, parts.day);
    if (isNaN(born.getTime())) return null;
    var today = new Date();
    var age = today.getFullYear() - born.getFullYear();
    if (
      today.getMonth() < born.getMonth() ||
      (today.getMonth() === born.getMonth() && today.getDate() < born.getDate())
    ) {
      age -= 1;
    }
    return age;
  }

  window.APP.Dates = {
    isoToPtBr: isoToPtBr,
    ptBrToIso: ptBrToIso,
    parseParts: parseParts,
    ageYears: ageYears
  };
})();
