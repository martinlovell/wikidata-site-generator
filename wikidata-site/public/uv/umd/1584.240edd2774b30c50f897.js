"use strict";(self.webpackChunkUV=self.webpackChunkUV||[]).push([[1584],{9292:(e,t,n)=>{n.d(t,{a:()=>r,b:()=>c,c:()=>a,d:()=>h,e:()=>f,f:()=>i,h:()=>o,i:()=>d,n:()=>s,p:()=>u,r:()=>l});var r=function(e){return"function"==typeof __zone_symbol__requestAnimationFrame?__zone_symbol__requestAnimationFrame(e):"function"==typeof requestAnimationFrame?requestAnimationFrame(e):setTimeout(e)},o=function(e){return!!e.shadowRoot&&!!e.attachShadow},i=function(e){var t=e.closest("ion-item");return t?t.querySelector("ion-label"):null},l=function(e,t,n,r,i){if(e||o(t)){var l=t.querySelector("input.aux-input");l||((l=t.ownerDocument.createElement("input")).type="hidden",l.classList.add("aux-input"),t.appendChild(l)),l.disabled=i,l.name=n,l.value=r||""}},a=function(e,t,n){return Math.max(e,Math.min(t,n))},c=function(e,t){if(!e){var n="ASSERT: "+t;throw console.error(n),new Error(n)}},s=function(e){return e.timeStamp||Date.now()},u=function(e){if(e){var t=e.changedTouches;if(t&&t.length>0){var n=t[0];return{x:n.clientX,y:n.clientY}}if(void 0!==e.pageX)return{x:e.pageX,y:e.pageY}}return{x:0,y:0}},d=function(e){var t="rtl"===document.dir;switch(e){case"start":return t;case"end":return!t;default:throw new Error('"'+e+'" is not a valid value for [side]. Use "start" or "end" instead.')}},h=function(e,t){var n=e._original||e;return{_original:e,emit:f(n.emit.bind(n),t)}},f=function(e,t){var n;return void 0===t&&(t=0),function(){for(var r=[],o=0;o<arguments.length;o++)r[o]=arguments[o];clearTimeout(n),n=setTimeout.apply(void 0,[e,t].concat(r))}}},1584:(e,t,n)=>{n.r(t),n.d(t,{ion_header:()=>d});var r=n(2085),o=n(9292),i=function(e,t,n,r){return new(n||(n=Promise))((function(o,i){function l(e){try{c(r.next(e))}catch(e){i(e)}}function a(e){try{c(r.throw(e))}catch(e){i(e)}}function c(e){e.done?o(e.value):new n((function(t){t(e.value)})).then(l,a)}c((r=r.apply(e,t||[])).next())}))},l=function(e,t){var n,r,o,i,l={label:0,sent:function(){if(1&o[0])throw o[1];return o[1]},trys:[],ops:[]};return i={next:a(0),throw:a(1),return:a(2)},"function"==typeof Symbol&&(i[Symbol.iterator]=function(){return this}),i;function a(i){return function(a){return function(i){if(n)throw new TypeError("Generator is already executing.");for(;l;)try{if(n=1,r&&(o=2&i[0]?r.return:i[0]?r.throw||((o=r.return)&&o.call(r),0):r.next)&&!(o=o.call(r,i[1])).done)return o;switch(r=0,o&&(i=[2&i[0],o.value]),i[0]){case 0:case 1:o=i;break;case 4:return l.label++,{value:i[1],done:!1};case 5:l.label++,r=i[1],i=[0];continue;case 7:i=l.ops.pop(),l.trys.pop();continue;default:if(!((o=(o=l.trys).length>0&&o[o.length-1])||6!==i[0]&&2!==i[0])){l=0;continue}if(3===i[0]&&(!o||i[1]>o[0]&&i[1]<o[3])){l.label=i[1];break}if(6===i[0]&&l.label<o[1]){l.label=o[1],o=i;break}if(o&&l.label<o[2]){l.label=o[2],l.ops.push(i);break}o[2]&&l.ops.pop(),l.trys.pop();continue}i=t.call(e,l)}catch(e){i=[6,e],r=0}finally{n=o=0}if(5&i[0])throw i[1];return{value:i[0]?i[1]:void 0,done:!0}}([i,a])}}},a=function(e){var t=document.querySelector(e+".ion-cloned-element");if(null!==t)return t;var n=document.createElement(e);return n.classList.add("ion-cloned-element"),n.style.setProperty("display","none"),document.body.appendChild(n),n},c=function(e){if(e){var t=e.querySelectorAll("ion-toolbar");return{el:e,toolbars:Array.from(t).map((function(e){var t=e.querySelector("ion-title");return{el:e,background:e.shadowRoot.querySelector(".toolbar-background"),ionTitleEl:t,innerTitleEl:t?t.shadowRoot.querySelector(".toolbar-title"):null,ionButtonsEl:Array.from(e.querySelectorAll("ion-buttons"))||[]}}))||[[]]}}},s=function(e,t){void 0===t?e.background.style.removeProperty("--opacity"):e.background.style.setProperty("--opacity",t.toString())},u=function(e,t){void 0===t&&(t=!0),(0,r.w)((function(){t?e.el.classList.remove("header-collapse-condense-inactive"):e.el.classList.add("header-collapse-condense-inactive")}))},d=function(){function e(e){(0,r.r)(this,e),this.collapsibleHeaderInitialized=!1,this.translucent=!1}return e.prototype.componentDidLoad=function(){return i(this,void 0,void 0,(function(){return l(this,(function(e){switch(e.label){case 0:return[4,this.checkCollapsibleHeader()];case 1:return e.sent(),[2]}}))}))},e.prototype.componentDidUpdate=function(){return i(this,void 0,void 0,(function(){return l(this,(function(e){switch(e.label){case 0:return[4,this.checkCollapsibleHeader()];case 1:return e.sent(),[2]}}))}))},e.prototype.componentDidUnload=function(){this.destroyCollapsibleHeader()},e.prototype.checkCollapsibleHeader=function(){return i(this,void 0,void 0,(function(){var e,t,n,o;return l(this,(function(i){switch(i.label){case 0:return e="condense"===this.collapse,(t=!(!e||"ios"!==(0,r.f)(this))&&e)||!this.collapsibleHeaderInitialized?[3,1]:(this.destroyCollapsibleHeader(),[3,3]);case 1:return!t||this.collapsibleHeaderInitialized?[3,3]:(n=this.el.closest("ion-app,ion-page,.ion-page,page-inner"),o=n?n.querySelector("ion-content"):null,[4,this.setupCollapsibleHeader(o,n)]);case 2:i.sent(),i.label=3;case 3:return[2]}}))}))},e.prototype.destroyCollapsibleHeader=function(){this.intersectionObserver&&(this.intersectionObserver.disconnect(),this.intersectionObserver=void 0),this.scrollEl&&this.contentScrollCallback&&(this.scrollEl.removeEventListener("scroll",this.contentScrollCallback),this.contentScrollCallback=void 0)},e.prototype.setupCollapsibleHeader=function(e,t){return i(this,void 0,void 0,(function(){var n,i=this;return l(this,(function(l){switch(l.label){case 0:return e&&t?(n=this,[4,e.getScrollElement()]):(console.error("ion-header requires a content to collapse, make sure there is an ion-content."),[2]);case 1:return n.scrollEl=l.sent(),(0,r.m)((function(){var e=t.querySelectorAll("ion-header"),n=Array.from(e).find((function(e){return"condense"!==e.collapse}));if(n&&i.scrollEl){var l=c(n),a=c(i.el);l&&a&&(u(l,!1),(0,r.m)((function(){var e=l.el.clientHeight;i.intersectionObserver=new IntersectionObserver((function(e){!function(e,t,n){(0,r.w)((function(){!function(e,t){if(e[0].isIntersecting){var n=100*(1-e[0].intersectionRatio)/75;s(t.toolbars[0],1===n?void 0:n)}}(e,t);var r=e[0],o=r.intersectionRect,i=o.width*o.height,l=r.rootBounds.width*r.rootBounds.height,a=0===i&&0===l,c=Math.abs(o.left-r.boundingClientRect.left),d=Math.abs(o.right-r.boundingClientRect.right);a||i>0&&(c>=5||d>=5)||(r.isIntersecting?(u(t,!1),u(n)):(0===o.x&&0===o.y||0!==o.width&&0!==o.height)&&(u(t),u(n,!1),s(t.toolbars[0],1)))}))}(e,l,a)}),{threshold:[.25,.3,.4,.5,.6,.7,.8,.9,1],rootMargin:"-"+e+"px 0px 0px 0px"}),i.intersectionObserver.observe(a.toolbars[0].el)})),i.contentScrollCallback=function(){!function(e,t){(0,r.m)((function(){var n=e.scrollTop,i=(0,o.c)(1,1+-n/500,1.1);(0,r.w)((function(){!function(e,t,n){void 0===e&&(e=[]),void 0===t&&(t=1),void 0===n&&(n=!1),e.forEach((function(e){var r=e.ionTitleEl,o=e.innerTitleEl;r&&"large"===r.size&&(o.style.transformOrigin="left center",o.style.transition=n?"all 0.2s ease-in-out":"",o.style.transform="scale3d("+t+", "+t+", 1)")}))}(t.toolbars,i)}))}))}(i.scrollEl,a)},i.scrollEl.addEventListener("scroll",i.contentScrollCallback))}})),(0,r.w)((function(){a("ion-title"),a("ion-back-button")})),this.collapsibleHeaderInitialized=!0,[2]}}))}))},e.prototype.render=function(){var e,t=(0,r.f)(this),n=this.collapse||"none";return(0,r.h)(r.H,{role:"banner",class:(e={},e[t]=!0,e["header-"+t]=!0,e["header-translucent"]=this.translucent,e["header-collapse-"+n]=!0,e["header-translucent-"+t]=this.translucent,e)})},Object.defineProperty(e.prototype,"el",{get:function(){return(0,r.d)(this)},enumerable:!0,configurable:!0}),Object.defineProperty(e,"style",{get:function(){return'ion-header{display:block;position:relative;-ms-flex-order:-1;order:-1;width:100%;z-index:10}ion-header ion-toolbar:first-child{padding-top:var(--ion-safe-area-top,0)}.header-md:after{left:0;bottom:-5px;background-position:left 0 top -2px;position:absolute;width:100%;height:5px;background-image:url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAHBAMAAADzDtBxAAAAD1BMVEUAAAAAAAAAAAAAAAAAAABPDueNAAAABXRSTlMUCS0gBIh/TXEAAAAaSURBVAjXYxCEAgY4UIICBmMogMsgFLtAAQCNSwXZKOdPxgAAAABJRU5ErkJggg==);background-repeat:repeat-x;content:""}:host-context([dir=rtl]) .header-md:after,[dir=rtl] .header-md:after{left:unset;right:unset;right:0;background-position:right 0 top -2px}.header-collapse-condense,.header-md[no-border]:after{display:none}'},enumerable:!0,configurable:!0}),e}()}}]);