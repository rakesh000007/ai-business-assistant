/* AI Chat page logic — talks to your existing Flask/Gemini backend. */

const CHAT_ENDPOINT = "/ai/api/gemini-chat";

const businessId =
  document.getElementById("businessId")?.value;

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("chatForm");
  const input = document.getElementById("chatInput");
  const window_ = document.getElementById("chatWindow");
  const empty = document.getElementById("chatEmpty");

  // --------------------------------------------------
  // CONVERSATION MEMORY
  // --------------------------------------------------
  // Stores previous user + AI messages during this chat.
  let conversationHistory = [];

  // Stores properties rejected by the customer
  let rejectedPropertyIds = [];

  // Stores the property/properties currently shown
  let currentPropertyIds = [];

  function scrollBottom() {
    window_.scrollTop = window_.scrollHeight;
  }

  function addCustomerMsg(text) {
    empty?.remove();

    const el = document.createElement("div");
    el.className = "msg msg-customer";

    el.innerHTML = `<div class="bubble"></div>`;

    el.querySelector(".bubble").textContent = text;

    window_.appendChild(el);
    scrollBottom();
  }

  function addAiMsg(text, properties) {
    const el = document.createElement("div");
    el.className = "msg msg-ai";

    el.innerHTML = `
      <div class="bubble-row">
        <span class="tl-icon icon-purple">
          <i class="bi bi-robot"></i>
        </span>
        <div class="bubble"></div>
      </div>
    `;

    el.querySelector(".bubble").textContent = text || "";

    // Render property cards dynamically
    (properties || []).forEach((p) => {
      const card = document.createElement("div");
      card.className = "glass-card property-card";

      card.innerHTML = `
        <h4>${p.title ?? "Property"}</h4>

        <span class="ptype">
          ${p.type ?? ""}
        </span>

        ${p.description
          ? `<p class="pdesc">${p.description}</p>`
          : ""
        }

        <ul>
          ${
            p.location || p.city
              ? `<li>
                  <i class="bi bi-geo-alt-fill"></i>
                  ${p.location ?? p.city}
                </li>`
              : ""
          }

          ${
            p.address
              ? `<li>
                  <i class="bi bi-signpost-2"></i>
                  ${p.address}
                </li>`
              : ""
          }

          ${
            p.bedrooms
              ? `<li>
                  <i class="bi bi-door-closed"></i>
                  ${p.bedrooms} Bedrooms
                </li>`
              : ""
          }

          ${
            p.bathrooms
              ? `<li>
                  <i class="bi bi-droplet"></i>
                  ${p.bathrooms} Bathrooms
                </li>`
              : ""
          }

          ${
            p.area || p.size
              ? `<li>
                  <i class="bi bi-rulers"></i>
                  ${p.area ?? p.size}
                </li>`
              : ""
          }

          ${
            p.price
              ? `<li class="mono">
                  <i class="bi bi-cash-stack"></i>
                  ${p.price}
                </li>`
              : ""
          }
        </ul>

        ${
          p.status
            ? `<span class="status ${String(p.status).toLowerCase()}">
                ${p.status}
              </span>`
            : ""
        }
      `;

      el.appendChild(card);
    });

    window_.appendChild(el);
    scrollBottom();
  }

  function addTyping() {
    const el = document.createElement("div");

    el.className = "msg msg-ai";
    el.id = "typingMsg";

    el.innerHTML = `
      <div class="bubble-row">
        <span class="tl-icon icon-purple">
          <i class="bi bi-robot"></i>
        </span>

        <div class="bubble">
          <span class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
          </span>
        </div>
      </div>
    `;

    window_.appendChild(el);
    scrollBottom();
  }

  async function sendMessage(text) {

    addCustomerMsg(text);
    addTyping();

    try {
      // --------------------------------------------------
      // CURRENT PROPERTY DATA
      // --------------------------------------------------
      // Gemini is responsible for understanding the
      // customer's intent. JavaScript does not decide
      // whether the customer rejected the property.
      // --------------------------------------------------

      console.log(
        "CURRENT PROPERTY IDS:",
        currentPropertyIds
      );
      // --------------------------------------------------
      // SEND PREVIOUS CONVERSATION MESSAGES
      // --------------------------------------------------

      const previousHistory = [...conversationHistory];

      const requestStart = performance.now();
      const res = await fetch(CHAT_ENDPOINT, {
        method: "POST",

        headers: {
          "Content-Type": "application/json"
        },

       body: JSON.stringify({
          message: text,
          conversation_history: previousHistory,
          rejected_property_ids: rejectedPropertyIds,
          current_property_ids: currentPropertyIds,
          business_id: businessId
       })
      });

      // --------------------------------------------------
      // GET RESPONSE AS TEXT FIRST
      // --------------------------------------------------

      const rawText = await res.text();
      const requestEnd = performance.now();

      console.log(
      "⏱️ BROWSER FETCH TIME:",
      ((requestEnd - requestStart) / 1000).toFixed(2),
      "seconds"
     );

      console.log(
        "AI API STATUS:",
        res.status
      );

      console.log(
        "AI API RESPONSE:",
        rawText
      );

      let data;

      try {

        data = JSON.parse(rawText);

      } catch (jsonError) {

        throw new Error(
          "Server did not return valid JSON: " +
          rawText
        );

      }

      // --------------------------------------------------
      // REMOVE TYPING INDICATOR
      // --------------------------------------------------

      document
        .getElementById("typingMsg")
        ?.remove();

      // --------------------------------------------------
      // CHECK BACKEND SUCCESS
      // --------------------------------------------------

      if (!res.ok || data.success === false) {

        console.error(
          "AI BACKEND ERROR:",
          data.message ||
          "Unknown server error"
        );

        addAiMsg(
          data.message ||
          "The assistant encountered an error while processing your request."
        );

        return;
      }

      // --------------------------------------------------
      // UPDATE CURRENT PROPERTY IDS
      // --------------------------------------------------
      // The backend sends the properties that were found
      // in this response.
      //
      // These become the properties that can be rejected
      // by the customer's NEXT response.
      // --------------------------------------------------

      currentPropertyIds = (data.properties || [])
        .map((p) => p.property_id)
        .filter((id) => id !== null && id !== undefined);

      rejectedPropertyIds =
        data.rejected_property_ids ||
        rejectedPropertyIds;
        
      console.log(
        "NEW CURRENT PROPERTY IDS:",
        currentPropertyIds
      );

      // --------------------------------------------------
      // SAVE CURRENT CONVERSATION
      // --------------------------------------------------

      conversationHistory.push({
        role: "user",
        content: text
      });

      conversationHistory.push({
        role: "assistant",
        content: data.response || ""
      });

      // --------------------------------------------------
      // DISPLAY AI RESPONSE
      // --------------------------------------------------

      addAiMsg(
        data.response,
        data.properties || []
      );

    } catch (err) {

      document
        .getElementById("typingMsg")
        ?.remove();

      console.error(
        "CHAT ERROR:",
        err
      );

      addAiMsg(
        "Sorry, something went wrong. Please check the server console."
      );
    }
  }

  // --------------------------------------------------
  // NORMAL MESSAGE SUBMIT
  // --------------------------------------------------

  form?.addEventListener("submit", (e) => {

    e.preventDefault();

    const text = input.value.trim();

    if (!text) return;

    input.value = "";

    sendMessage(text);
  });

  // --------------------------------------------------
  // QUICK SUGGESTION BUTTONS
  // --------------------------------------------------

  document
    .querySelectorAll(".suggestion-chip")
    .forEach((chip) => {

      chip.addEventListener("click", () => {

        const text = chip.dataset.text;

        if (text) {
          sendMessage(text);
        }

      });

    });

});