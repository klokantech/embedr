(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
var CloseButton = React.createClass({displayName: "CloseButton",
  render: function() {
    if (this.props.dark) {
      imageSrc = 'static/img/close_dark.png'
    }
    else {
      imageSrc = 'static/img/close.png'
    }
    return (
      React.createElement("div", {className: "button__close", onClick: this.props.onClick}, React.createElement("img", {src: imageSrc}))
    )
  }
})

module.exports = CloseButton;

},{}],2:[function(require,module,exports){
var EmbedButton = React.createClass({displayName: "EmbedButton",
  render: function() {
    return (
      React.createElement("a", {className: "button__embed", href: "#", onClick: this.props.togglePopup}, 
        React.createElement("img", {src: "static/img/embed.png"})
      )
    )
  }
});

module.exports = EmbedButton;

},{}],3:[function(require,module,exports){
var CloseButton = require('./close_button.jsx')
var IIIFImage = require('./iiif_image.jsx');

var EmbedPopup = React.createClass({displayName: "EmbedPopup",
  getProportion: function() {
    if (this.props.result) {
      var meta = JSON.parse(this.props.result.image_meta)[0];
      return (meta.height/meta.width*100)+"%";
    } else {
      return (this.props.height/this.props.width*100)+"%";
    }
  },
  render: function() {
    var id = this.props.id ? this.props.id : this.props.result.id;
    var proportion = this.getProportion();
    var embedLink = "http://media.embedr.eu/" + id;
    var embedText = '<div class="embdr_wrapper" style="position: relative; padding-bottom: '+proportion+'; padding-top: 0px; height: 0;"><iframe style="border: 0; position: absolute; top: 0; left: 0; width: 100%; height: 100%;" src="' + embedLink + '">Your browser doesn\'t support iFrames.</iframe></div>'
    return (
      React.createElement("div", {className: "embed__popup"}, 
        React.createElement(CloseButton, {onClick: this.props.close}), 
        React.createElement("p", {className: "embed__title"}, "Embed this image"), 
        React.createElement("p", null, "First choose your platform:"), 
        React.createElement("div", {className: "embed__option"}, 
          React.createElement("p", {className: "embed__subtitle"}, "Embed on social media"), 
          React.createElement("p", {className: "embed__callout"}, React.createElement("img", {src: "static/img/share_small.png", className: "embed__icon"}), "Copy the URL in the address bar.")

        ), 
        React.createElement("div", {className: "embed__option"}, 
          React.createElement("p", {className: "embed__subtitle"}, "Embed on website or blog"), 
          React.createElement("p", {className: "embed__callout"}, React.createElement("img", {src: "static/img/embed_small.png", className: "embed__icon"}), "Copy the HTML code below"), 
          React.createElement("textarea", {className: "embed__box", rows: "6", id: "text-copy"}, 
            embedText
          )
        ), 
        React.createElement("a", {href: "http://embedr.eu/content/how-to-embed"}, "More information about embedding")
      )
    )
  }
});

module.exports = EmbedPopup;

},{"./close_button.jsx":1,"./iiif_image.jsx":4}],4:[function(require,module,exports){
var IIIFImage = React.createClass({displayName: "IIIFImage",
  makeSource: function() {
    var server = this.props.server;
    var id = this.props.id;
    var region = this.props.region || "full";
    var size = this.props.size || "1000,";
    var rotation = this.props.rotation || "0";
    var quality = this.props.quality || "native";
    var format = this.props.format || "jpg";
    return server+"/"+id+"/"+region+"/"+size+"/"+rotation+"/"+quality + "." +format;
  },
  render: function() {
    var source = this.makeSource();
    return (
      React.createElement("img", {src: source})
    )
  }
});

module.exports = IIIFImage;

},{}],5:[function(require,module,exports){
var RegionButton = React.createClass({displayName: "RegionButton",
  makeIIIF: function(rect) {
    this.props.setRegion(rect.x+','+rect.y+','+rect.width+','+rect.height);
    this.boxDrawer.exitEditMode();
    document.body.style.cursor = "auto";
    $('.osd-select-rectangle').remove();
  },
  startSelection: function() {
    var self = this;
    if (!self.boxDrawer) {
      self.boxDrawer = osdRegionRectTool({
        osd: OpenSeadragon,
        viewer: viewer,
        onDrawFinish: function(rect) { self.makeIIIF(rect) }
      });
    }
    document.body.style.cursor = "crosshair";
    this.boxDrawer.enterEditMode();
  },
  render: function() {
    return (
      React.createElement("a", {className: "button__region", href: "#", onClick: this.startSelection}, 
        React.createElement("img", {src: "static/img/crop.png"})
      )
    )
  }
});

module.exports = RegionButton;

},{}],6:[function(require,module,exports){
var CloseButton = require('./close_button.jsx')
var IIIFImage = require('./iiif_image.jsx');

var RegionPopup = React.createClass({displayName: "RegionPopup",
  getInitialState: function() {
    var region = this.props.region.split(',')
    return {
      width: region[2],
      height: region[3],
      ratio: region[2]/region[3]
    };
  },
  validateSize: function(height, width) {
    var ratio = this.state.ratio;
    if (height > width && height > 2056) {
      height = 2056;
      width = height * ratio;
    }
    else if (width > height && width > 2056) {
      width = 2056;
      height = width / ratio;
    }
    return {height: Math.round(height), width: Math.round(width)};
  },
  setHeight: function(event) {
    var height = event.target.value;
    var width = height * this.state.ratio;
    this.setState(this.validateSize(height,width));
  },
  setWidth: function(event) {
    var width = event.target.value;
    var height = width / this.state.ratio;
    this.setState(this.validateSize(height,width));
  },
  render: function() {
    var id = this.props.id ? this.props.id : this.props.result.id;
    var metadataText = "Detail of "+this.props.metadataText;
    return (
      React.createElement("div", {className: "embed__popup"}, 
        React.createElement(CloseButton, {onClick: this.props.close}), 
        React.createElement("p", {className: "embed__title"}, "Embed this selection"), 
        React.createElement("p", null, "Copy the code below to your website or blog"), 
        React.createElement(RegionBox, {height: this.state.height, width: this.state.width, region: this.props.region, id: this.props.id, metadataText: metadataText}), 
        React.createElement("div", {className: "embed__option"}, 
          React.createElement("p", {className: "embed__resize"}, 
            "Adjust the size of the image", 
            React.createElement("input", {id: "emded_height", value: this.state.height, onChange: this.setHeight}), 
            "x", 
            React.createElement("input", {id: "emded_width", value: this.state.width, onChange: this.setWidth})
          ), 
          React.createElement("p", {className: "embed__resize"}, "The width and height have a maximum of 2056 pixels")
        ), 
        React.createElement(IIIFImage, {id: id, region: this.props.region, server: "http://iiif.embedr.eu", size: "!400,300"}), 
        React.createElement("p", null, React.createElement("a", {href: "http://embedr.eu/content/how-to-embed"}, "More information about embedding"))
      )
    )
  }
});

var RegionBox = React.createClass({displayName: "RegionBox",
  render: function() {
    var embedText = "<div id='embedr_img'><img src='http://iiif.embedr.eu/"+this.props.id+"/"+this.props.region+"/"+this.props.width+","+this.props.height+"/0/native.jpg'/><p>"+this.props.metadataText+"</p></div>";
    return (
      React.createElement("textarea", {className: "embed__box", rows: "6", id: "text-copy", value: embedText, readOnly: true}
      )
    )
  }
});

module.exports = RegionPopup;

},{"./close_button.jsx":1,"./iiif_image.jsx":4}],7:[function(require,module,exports){
var EmbedButton = require('./embed_button.jsx')
var EmbedPopup = require('./embed_popup.jsx')
var RegionButton = require('./region_button.jsx')
var RegionPopup = require('./region_popup.jsx')

var makeLicenseHtml = function(license) {
  if (license.indexOf('publicdomain') > 0) {
    return "<img src='/static/img/pd.png' /> <a href='"+license+"'>No rights reserved.</a>"
  } else {
    return "<img src='/static/img/cc.png' /> <a href='"+license+"'>Some rights reserved.</a>"
  }
}

var Viewer = React.createClass({displayName: "Viewer",
  processMetadata: function(res) {
    var imageData = res.sequences[0].canvases[0];
    var height = imageData.height;
    var width = imageData.width;
    var title = res.label;
    var author = '';
    var institution = '';
    var institutionUrl = '';
    res.metadata.forEach(function(metadata) {
      if (metadata.label == 'Author') {
        author = metadata.value;
      }
      else if (metadata.label == 'Institution') {
        institution = metadata.value;
      }
      else if (metadata.label == 'Institution link') {
        institutionUrl = metadata.value;
      }
    });
    var institutionLink = "<a href='"+institutionUrl+"' target='_blank'>"+institution+"</a>";
    var license = res.license;
    var licenseHtml = makeLicenseHtml(license);
    var metadataText = "'"+title+"' | ";
    var metadataText = metadataText+author+" | ";
    var metadataText = metadataText+institutionLink+" | ";
    var metadataText = metadataText+licenseHtml;
    this.setState({
      height: height,
      width: width,
      metadataText: metadataText
    });
  },
  componentDidMount: function() {
    var apiUrl = "http://media.embedr.eu/"+this.props.id+"/manifest.json";
    $.getJSON(apiUrl, function(res) {
      this.processMetadata(res);
    }.bind(this));
  },
  getInitialState: function() {
    return {
      showEmbedPopup: false,
      showRegionPopup: false,
      height: 100,
      width: 100,
      region: 'full'
    };
  },
  toggleEmbedPopup: function(e) {
    e.preventDefault();
    this.setState({showEmbedPopup: !this.state.showEmbedPopup});
  },
  setRegion: function(region) {
    this.setState({region: region});
    this.setState({showRegionPopup: !this.state.showRegionPopup});
  },
  toggleRegionPopup: function(e) {
    e.preventDefault();
    this.setState({showRegionPopup: !this.state.showRegionPopup});
  },
  render: function() {
    return (
      React.createElement("div", {className: "viewer"}, 
        React.createElement("div", {className: "viewer__toolbar"}, 
          React.createElement(EmbedButton, {togglePopup: this.toggleEmbedPopup}), 
          React.createElement("div", {className: "button__zoom"}, 
            React.createElement("a", {id: "zoom-in-button", href: "#"}, 
              React.createElement("img", {src: "static/img/zoom-in.png"})
            )
          ), 
          React.createElement("div", {className: "button__zoom--out"}, 
            React.createElement("a", {id: "zoom-out-button", href: "#"}, 
              React.createElement("img", {src: "static/img/zoom-out.png"})
            )
          ), 
          React.createElement(RegionButton, {setRegion: this.setRegion})
        ), 

         this.state.showEmbedPopup ? React.createElement(EmbedPopup, {width: this.state.width, height: this.state.height, id: this.props.id, close: this.toggleEmbedPopup}) : null, 

         this.state.showRegionPopup ? React.createElement(RegionPopup, {region: this.state.region, id: this.props.id, close: this.toggleRegionPopup, metadataText: this.state.metadataText}) : null, 
        React.createElement(MetadataField, {text: this.state.metadataText})
      )
    )
  }
});

var MetadataField = React.createClass({displayName: "MetadataField",
  getInitialState: function() {
    return {
      hidden: false
    }
  },
  hide: function() {
    this.setState({hidden: true})
  },
  render: function() {
    if (this.state.hidden) {
      return null;
    }
    return (
      React.createElement("div", {id: "title"}, 
        React.createElement("span", {dangerouslySetInnerHTML: {__html: this.props.text}}), 
        React.createElement("a", {href: "#", id: "close", onClick: this.hide})
      )
    )
  }
});

module.exports = Viewer;

},{"./embed_button.jsx":2,"./embed_popup.jsx":3,"./region_button.jsx":5,"./region_popup.jsx":6}],8:[function(require,module,exports){
var Viewer = require('./components/viewer.jsx')
//Export to window so it can be called in a Flask template.
window.Viewer = Viewer;

$(function(){
  $('#map').on('mouseover', function(e) {
    $('.viewer__toolbar').show();
  });
  $('#map').on('mouseout', function(e) {
    if ($(e.toElement).closest('.viewer__toolbar').length > 0) return;
    $('.viewer__toolbar').hide();
  });
});

},{"./components/viewer.jsx":7}]},{},[8]);
