
var map = d3.geomap.choropleth()
    .geofile('data/usa_states.json')
    .projection(d3.geo.albersUsa)
    .column('dollars')
    .unitId('state')
    .scale(1000)
    .legend(true)
    .colors(colorbrewer.YlGnBu[9])
    .format(formatCurrency);

var companies = [];

function formatCurrency(d) {
    if (d < 1e6) {
        d = d / 1000;
        return '$' + d3.format(',.01f')(d) + 'k';
    } else {
        d = d / 1e6;
        return '$' + d3.format(',.01f')(d) + 'M';
    }
}

function formatCount(d) {
    return d3.format(',.00f')(d);
}

function addToSelect(companies) {
    $.each(companies, function (index, d) {
        $('#select-company').append($('<option/>', { 
            value: d.id,
            text : d.name 
        }));
    });   
}

function slugify(text)
{
  return text.toString().toLowerCase()
    .replace(/\s+/g, '-')           // Replace spaces with -
    .replace(/[^\w\-]+/g, '')       // Remove all non-word chars
    .replace(/\-\-+/g, '-')         // Replace multiple - with single -
    .replace(/^-+/, '')             // Trim - from start of text
    .replace(/-+$/, '');            // Trim - from end of text
}

function displayCompanyInfo(id) {
    var company = getCompanyById(id);

    if (id == -1) {
        window.location.hash = '';
    } else {
        window.location.hash = '#' + slugify(company.name);
    }

    // Update template
    $("#payments-phys").text(formatCount(company.payments_phys)); 
    $("#payments-hosp").text(formatCount(company.payments_hosp)); 
    $("#dollars-total").text(formatCurrency(company.dollars_total)); 
    $("#dollars-phys").text(formatCurrency(company.dollars_phys)); 
    $("#company-name").text(company.name); 
    $("#dollars-hosp").text(formatCurrency(company.dollars_hosp)); 
    $("#product-count").text(company.products.length); 
    $("#product-list").text(company.products.join(", ")); 
    $("#location").text(company.location);

    $(".products").show();
    $(".location").show();

    if (!company.location) {
        $('.location').addClass("hide");
    } else {
        $(".location").removeClass("hide")
    }
    if (company.payments_phys === 0) {
        $('.physician').addClass("null");
    } else {
        $(".physician").removeClass("null")
    }
    if (company.payments_hosp === 0) {
        $('.hospital').addClass("null");
    } else {
        $(".hospital").removeClass("null")
    }
    if (company.products.length === 0) {
        $('.products').addClass("null");
    } else {
        $(".products").removeClass("null")
    }

    // Update map data
    var map = d3.geomap.choropleth()
        .geofile('data/usa_states.json')
        .projection(d3.geo.albersUsa)
        .column('dollars')
        .unitId('state')
        .scale(1000)
        .legend(true)
        .colors(colorbrewer.GnBu[9])
        .format(formatCurrency);

    url = 'data/bycompany/' + company.id + ".csv";

    d3.csv(url, function(error, data) {
        $('#map').html("");
        d3.select('#map')
            .datum(data)
            .call(map.draw, map);
    });     
}

function getCompanyById(id) {
    var company;
    for (var i = companies.length - 1; i >= 0; i--) {
        var _company = companies[i];
        if (_company.id == id) {
            company = _company;
            break;
        }
    };
    if (company) {
        return company
    } else {
        console.log("Error, id not found!", id)
    }
}

function getCompanyByHash(hash) {
    var company;
    var companySlug = hash.replace("#","");
    if (companySlug === "") {
        return null;
    }

    for (var i = companies.length - 1; i >= 0; i--) {
        var _company = companies[i];
        if (slugify(_company.name) == companySlug) {
            company = _company;
            break;
        }
    };
    if (company) {
        return company
    } else {
        console.log("Error, company not found: ", hash)
    }
}

var selectizeElem;

function activateSelectize() {
    selectizeElem = $('#select-company').selectize({
        create: true,
        closeAfterSelect: true,
        onChange: displayCompanyInfo
    });
}

$(document).ready(function() {

    var request = $.ajax({
        url: "data/companies.json",
        type: "GET",
        dataType: "json"
    }).success(function(data, status, xhr) {
        addToSelect(data);
        activateSelectize();
        companies = data;

        // determine starting state
        var startId = -1;
        var startCompany = getCompanyByHash(window.location.hash);
        if (startCompany) { startId = startCompany.id; }
        selectizeElem[0].selectize.setValue(startId);

        displayCompanyInfo(startId);

    }).fail(function(jqXHR, textStatus) {
        console.log("Request failed: " + textStatus);
    });
});
