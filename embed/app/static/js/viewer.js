(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
var EmbedButton = React.createClass({displayName: "EmbedButton",
  render: function() {
    return (
      React.createElement("a", {className: "button__embed", href: "#", onClick: this.props.togglePopup}, 
        React.createElement("img", {src: "/images/embed.png"})
      )
    )
  }
});

module.exports = EmbedButton;

},{}],2:[function(require,module,exports){
var IIIFImage = require('./iiif_image.jsx');

var EmbedPopup = React.createClass({displayName: "EmbedPopup",
  render: function() {
    var embedLink = "http://media.embedr.eu/" + this.props.id;
    var embedText = "<iframe src=\"" + embedLink + "\"></iframe>"
    return (
      React.createElement("div", {className: "embed__popup"}, 
        React.createElement("div", {className: "button__close", onClick: this.props.close}, "X"), 
        React.createElement("strong", null, "Embed this image"), 
        React.createElement("p", null, "Copy the HTML code below to your website or blog. ", React.createElement("a", {href: "#"}, "Click here for more information.")), 
        React.createElement("textarea", {className: "embed__box", rows: "6", id: "text-copy"}, 
          embedText
        ), 
        React.createElement("a", {href: "#", className: "button__copy", id: "button-copy", "data-clipboard-target": "text-copy"}, "Copy"), 
        React.createElement("div", null, 
          React.createElement("label", null, "Show preview")
        ), 
        React.createElement(IIIFImage, {server: "http://iiif.embedr.eu", id: this.props.id, size: "400,150"})
      )
    )
  }
});

module.exports = EmbedPopup;

},{"./iiif_image.jsx":3}],3:[function(require,module,exports){
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

},{}],4:[function(require,module,exports){
var InformationButton = React.createClass({displayName: "InformationButton",
  render: function() {
    return (
      React.createElement("a", {className: "button__metadata", href: "#", onClick: this.props.togglePopup}, 
        React.createElement("img", {src: "/images/metadata.png"})
      )
    )
  }
});

module.exports = InformationButton;

},{}],5:[function(require,module,exports){
var InformationPopup = React.createClass({displayName: "InformationPopup",
  render: function() {
    return (
      React.createElement("div", {className: "metadata__popup"}
      )
    )
  }
});

module.exports = InformationPopup;

},{}],6:[function(require,module,exports){
var EmbedButton = require('./embed_button.jsx')
var EmbedPopup = require('./embed_popup.jsx')
var InformationButton = require('./information_button.jsx')
var InformationPopup = require('./information_popup.jsx')

var Viewer = React.createClass({displayName: "Viewer",
  getInitialState: function() {
    return {
      showEmbedPopup: false,
      showInfoPopup: false
    };
  },
  toggleEmbedPopup: function(e) {
    e.preventDefault();
    this.setState({showEmbedPopup: !this.state.showEmbedPopup});
  },
  toggleInfoPopup: function(e) {
    e.preventDefault();
    // Leaving this is in case we do switch to a React popup.
    // this.setState({showInfoPopup: !this.state.showInfoPopup});
    $('#title').toggle();
  },
  render: function() {
    return (
      React.createElement("div", {className: "viewer"}, 
        React.createElement("div", {className: "viewer__toolbar"}, 
          React.createElement(EmbedButton, {togglePopup: this.toggleEmbedPopup}), 
          React.createElement("div", {className: "button__zoom"}, 
            React.createElement("a", {id: "zoom-in-button", href: "#"}, 
              React.createElement("img", {src: "/images/zoom-in.png"})
            )
          ), 
          React.createElement("div", {className: "button__zoom--out"}, 
            React.createElement("a", {id: "zoom-out-button", href: "#"}, 
              React.createElement("img", {src: "/images/zoom-out.png"})
            )
          ), 
          React.createElement(InformationButton, {togglePopup: this.toggleInfoPopup})
        ), 
         this.state.showEmbedPopup ? React.createElement(EmbedPopup, {id: this.props.id, close: this.toggleEmbedPopup}) : null, 
         this.state.showInfoPopup ? React.createElement(InformationPopup, {id: this.props.id, close: this.toggleInfoPopup}) : null
      )
    )
  }
});

module.exports = Viewer;

},{"./embed_button.jsx":1,"./embed_popup.jsx":2,"./information_button.jsx":4,"./information_popup.jsx":5}],7:[function(require,module,exports){
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
