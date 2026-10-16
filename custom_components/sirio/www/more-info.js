// Shows the manual paragraph inside the parameter dialog.
// Home Assistant does not render entity attributes there.
if (!customElements.get("more-info-sirio-manual")) {
  class SirioManualMoreInfo extends HTMLElement {
    set hass(value) {
      this._hass = value;
    }

    set stateObj(value) {
      this._state = value;
      this._draw();
    }

    connectedCallback() {
      this._draw();
      const content = this.closest(".content");
      const host = this.closest("more-info-content");
      if (!content || !host) {
        return;
      }
      host.style.order = "1";
      const history = content.querySelector("ha-more-info-history");
      const logbook = content.querySelector("ha-more-info-logbook");
      if (history) {
        history.style.order = "2";
      }
      if (logbook) {
        logbook.style.order = "3";
      }
    }

    _section(heading, text) {
      const block = document.createElement("div");
      const title = document.createElement("div");
      title.textContent = heading;
      title.style.fontWeight = "600";
      title.style.color = "var(--secondary-text-color)";
      title.style.marginBottom = "6px";
      const body = document.createElement("div");
      body.textContent = text;
      block.append(title, body);
      return block;
    }

    _draw() {
      const attrs = this._state?.attributes || {};
      const russian = attrs.manual_ru;
      const english = attrs.manual;
      if (!russian && !english) {
        this.replaceChildren();
        return;
      }
      const box = document.createElement("div");
      box.style.margin = "0 0 16px";
      box.style.padding = "12px 16px";
      box.style.borderRadius = "12px";
      box.style.background = "var(--secondary-background-color, rgba(0,0,0,0.04))";
      box.style.color = "var(--primary-text-color)";
      box.style.fontSize = "var(--ha-font-size-m, 14px)";
      box.style.lineHeight = "1.45";
      box.style.whiteSpace = "pre-wrap";
      box.style.display = "flex";
      box.style.flexDirection = "column";
      box.style.gap = "14px";
      if (english) {
        box.append(this._section("EN:", english));
      }
      if (russian) {
        box.append(this._section("RU:", russian));
      }
      this.replaceChildren(box);
    }
  }

  customElements.define("more-info-sirio-manual", SirioManualMoreInfo);
}
