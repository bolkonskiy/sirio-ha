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

    _draw() {
      const text = this._state?.attributes?.manual;
      if (!text) {
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
      const title = document.createElement("div");
      title.textContent = "Manual";
      title.style.fontSize = "var(--ha-font-size-s, 12px)";
      title.style.fontWeight = "600";
      title.style.letterSpacing = "0.04em";
      title.style.textTransform = "uppercase";
      title.style.color = "var(--secondary-text-color)";
      title.style.marginBottom = "6px";
      const body = document.createElement("div");
      body.textContent = text;
      box.append(title, body);
      this.replaceChildren(box);
    }
  }

  customElements.define("more-info-sirio-manual", SirioManualMoreInfo);
}
