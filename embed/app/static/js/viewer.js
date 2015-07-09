(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
var CloseButton = React.createClass({displayName: "CloseButton",
  render: function() {
    return (
      React.createElement("div", {className: "button__close", onClick: this.props.onClick}, React.createElement("img", {src: "/static/img/close.png"}))
    )
  }
})

module.exports = CloseButton;

},{}],2:[function(require,module,exports){
var EmbedButton = React.createClass({displayName: "EmbedButton",
  render: function() {
    return (
      React.createElement("a", {className: "button__embed", href: "#", onClick: this.props.togglePopup}, 
        React.createElement("img", {src: "/static/img/embed.png"})
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
        React.createElement("p", null, "Copy the HTML code below to your website or blog. ", React.createElement("a", {href: "#"}, "Click here for more information.")), 
        React.createElement("textarea", {className: "embed__box", rows: "6", id: "text-copy"}, 
          embedText
        ), 
        React.createElement("textarea", {className: "embed__box", rows: "3", id: "text-copy"}, 
          embedLink
        ), 
        React.createElement("a", {href: "#", className: "button__copy", id: "button-copy", "data-clipboard-target": "text-copy"}, "copy")
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
var InformationButton = React.createClass({displayName: "InformationButton",
  render: function() {
    return (
      React.createElement("a", {className: "button__metadata", href: "#", onClick: this.props.togglePopup}, 
        React.createElement("img", {src: "/static/img/metadata.png"})
      )
    )
  }
});

module.exports = InformationButton;

},{}],6:[function(require,module,exports){
var EmbedButton = require('./embed_button.jsx')
var EmbedPopup = require('./embed_popup.jsx')
var InformationButton = require('./information_button.jsx')

var Viewer = React.createClass({displayName: "Viewer",
  componentDidMount: function() {
    var apiUrl = "http://iiif.embedr.eu/"+this.props.id+"/info.json";
    $.getJSON(apiUrl, function(res) {
      console.log(res);
      this.setState({
        height: res.height,
        width: res.width
      });
    }.bind(this));
  },
  getInitialState: function() {
    return {
      showEmbedPopup: false,
      height: 100,
      width: 100
    };
  },
  toggleEmbedPopup: function(e) {
    e.preventDefault();
    this.setState({showEmbedPopup: !this.state.showEmbedPopup});
  },
  render: function() {
    return (
      React.createElement("div", {className: "viewer"}, 
        React.createElement("div", {className: "viewer__toolbar"}, 
          React.createElement(EmbedButton, {togglePopup: this.toggleEmbedPopup}), 
          React.createElement("div", {className: "button__zoom"}, 
            React.createElement("a", {id: "zoom-in-button", href: "#"}, 
              React.createElement("img", {src: "/static/img/zoom-in.png"})
            )
          ), 
          React.createElement("div", {className: "button__zoom--out"}, 
            React.createElement("a", {id: "zoom-out-button", href: "#"}, 
              React.createElement("img", {src: "/static/img/zoom-out.png"})
            )
          )
        ), 
         this.state.showEmbedPopup ? React.createElement(EmbedPopup, {width: this.state.width, height: this.state.height, id: this.props.id, close: this.toggleEmbedPopup}) : null
      )
    )
  }
});

module.exports = Viewer;

},{"./embed_button.jsx":2,"./embed_popup.jsx":3,"./information_button.jsx":5}],7:[function(require,module,exports){
var Viewer = require('./components/viewer.jsx')
//Export to window so it can be called in a Flask template.
window.Viewer = Viewer;

$(function(){
  $('#map').on('mouseover', function(e) {
    $('#viewer').show();
  });
  $('#map').on('mouseout', function(e) {
    if ($(e.toElement).closest('#viewer').length > 0) return;
    $('#viewer').hide();
  });
});

},{"./components/viewer.jsx":6}]},{},[7]);
