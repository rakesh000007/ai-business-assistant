/* AI Call Assistant — Live Speech + AI Backend */

document.addEventListener("DOMContentLoaded", () => {

    const CHAT_ENDPOINT = "/ai/api/chat";

    const businessId =
        document.getElementById("businessId")?.value;
        

    const startBtn =
        document.getElementById("startCallBtn");

    const endBtn =
        document.getElementById("endCallBtn");

    const callStatus =
        document.getElementById("callStatus");

    const callTitle =
        document.getElementById("callTitle");

    const transcriptContent =
        document.getElementById("transcriptContent");

    const callOrb =
        document.getElementById("callOrb");

    



    // --------------------------------------------------
    // CONVERSATION MEMORY
    // --------------------------------------------------

    let conversationHistory = [];

    let rejectedPropertyIds = [];

    let currentPropertyIds = [];


   // --------------------------------------------------
   // SPEECH / RECORDING STATE
   // --------------------------------------------------

     let mediaRecorder = null;

     let audioChunks = [];

     let isCalling = false;

     let isProcessing = false;

    let isRecording = false;

    let restartTimer = null;    

    // --------------------------------------------------
    // AI MESSAGE QUEUE
    // --------------------------------------------------
    // If the customer speaks again while AI is responding,
    // the message is stored instead of being lost.
    // --------------------------------------------------

    let aiMessageQueue = [];


    // --------------------------------------------------
    // LIVE SPEECH ELEMENT
    // --------------------------------------------------

    let liveSpeechElement = null;

let deepgramSocket = null;
let pendingDeepgramTranscript = "";
let deepgramKeepAliveTimer = null;

// --------------------------------------------------
// GEMINI LIVE STATE
// --------------------------------------------------

let geminiSocket = null;
let geminiAudioContext = null;
let geminiPlaybackTime = 0;
let geminiSetupComplete = false;

let geminiMicStream = null;
let geminiMicSource = null;
let geminiMicProcessor = null;
let geminiMicAudioContext = null;
let geminiMicrophoneActive = false;
let geminiOutputTranscript = "";
let geminiInputTranscript = "";
let geminiConversationTranscript = "";
let savedCustomerId = null;

let excludedPropertyIds = [];
let currentPropertyId = null;

let lastPropertySearch = {
    city: null,
    property_type: null,
    bedrooms: null,
    budget: null
};
    // --------------------------------------------------
    // ADD MESSAGE TO TRANSCRIPT
    // --------------------------------------------------

    function addTranscript(
        text,
        type = "customer"
    ) {

        const message =
            document.createElement("div");

        message.className =
            `voice-message ${type}`;

        message.textContent =
            text;

        transcriptContent.appendChild(
            message
        );

        transcriptContent.scrollTop =
            transcriptContent.scrollHeight;

    }


    // --------------------------------------------------
    // SHOW LIVE SPEECH
    // --------------------------------------------------

    function showLiveSpeech(text) {

        if (!liveSpeechElement) {

            liveSpeechElement =
                document.createElement("div");

            liveSpeechElement.className =
                "voice-message customer live-speech";

            transcriptContent.appendChild(
                liveSpeechElement
            );
        }

        liveSpeechElement.textContent =
            text;

        transcriptContent.scrollTop =
            transcriptContent.scrollHeight;

    }


    // --------------------------------------------------
    // REMOVE LIVE SPEECH
    // --------------------------------------------------

    function removeLiveSpeech() {

        if (liveSpeechElement) {

            liveSpeechElement.remove();

            liveSpeechElement = null;

        }

    }


    // --------------------------------------------------
    // PROCESS ONE AI MESSAGE
    // --------------------------------------------------

    async function processAIMessage(text) {

        if (!text || !text.trim()) {
            return;
        }

        isProcessing = true;

        callStatus.textContent =
            "AI is thinking...";


        try {

            console.log(
                "SENDING VOICE MESSAGE:",
                text
            );


            // --------------------------------------------------
            // CHECK PROPERTY REJECTION
            // --------------------------------------------------

            const normalizedText =
                text
                    .toLowerCase()
                    .trim()
                    .replace(
                        /['’]/g,
                        ""
                    )
                    .replace(
                        /[^\w\s]/g,
                        ""
                    )
                    .replace(
                        /\s+/g,
                        " "
                    );


            const negativeResponses = [
                "no",
                "nope",
                "nah",
                "not interested",
                "im not interested",
                "i am not interested",
                "less interested",
                "not very interested",
                "not really interested",
                "not that interested",
                "no thanks",
                "not for me",
                "i dont want it",
                "i don't want it",
                "i do not want it",
                "i dont like it",
                "i don't like it",
                "i do not like it",
                "i didnt like it",
                "i didn't like it",
                "i dont like this",
                "i don't like this",
                "i do not like this",
                "i didnt like this",
                "i didn't like this",
                "i didnt trust",
                "i didn't trust",
                "i dont trust",
                "i don't trust",
                "i do not trust",
                "dont want this",
                "do not want this",
                "dont like this",
                "do not like this"
            ];

            const isNegativeResponse =
                negativeResponses.includes(
                    normalizedText
                ) ||
                normalizedText.includes(
                    "not interested"
                ) ||
                normalizedText.includes(
                    "less interested"
                ) ||
                normalizedText.includes(
                    "didnt like it"
                ) ||
                normalizedText.includes(
                    "didn't like it"
                ) ||
                normalizedText.includes(
                    "dont like it"
                ) ||
                normalizedText.includes(
                    "don't like it"
                ) ||
                normalizedText.includes(
                    "do not like it"
                );


            console.log(
                "NORMALIZED CUSTOMER RESPONSE:",
                normalizedText
            );

            console.log(
                "IS NEGATIVE RESPONSE:",
                isNegativeResponse
            );

            console.log(
                "CURRENT PROPERTY IDS:",
                currentPropertyIds
            );

            console.log(
                "REJECTED PROPERTY IDS:",
                rejectedPropertyIds
            );

            // --------------------------------------------------
            // SEND TO EXISTING AI BACKEND
            // --------------------------------------------------

            const previousHistory =
                [...conversationHistory];


            const response =
                await fetch(
                    CHAT_ENDPOINT,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            message:
                                text,

                            conversation_history:
                                previousHistory,

                            rejected_property_ids:
                                rejectedPropertyIds,

                            business_id:
                                businessId

                        })
                    }
                );


            // --------------------------------------------------
            // READ SERVER RESPONSE
            // --------------------------------------------------

            const rawText =
                await response.text();


            console.log(
                "AI API STATUS:",
                response.status
            );


            console.log(
                "AI API RESPONSE:",
                rawText
            );


            let data;


            try {

                data =
                    JSON.parse(rawText);

            } catch (error) {

                throw new Error(
                    "Server did not return valid JSON."
                );

            }


            // --------------------------------------------------
            // BACKEND ERROR
            // --------------------------------------------------

            if (
                !response.ok ||
                data.success === false
            ) {

                addTranscript(
                    data.message ||
                    "The AI assistant encountered an error.",
                    "ai"
                );

                return;

            }


            // --------------------------------------------------
            // UPDATE CURRENT PROPERTY IDS
            // --------------------------------------------------

            currentPropertyIds =
                (data.properties || [])
                    .map(
                        (property) =>
                            property.property_id
                    )
                    .filter(
                        (id) =>
                            id !== null &&
                            id !== undefined
                    );


            console.log(
                "CURRENT PROPERTY IDS:",
                currentPropertyIds
            );
            // --------------------------------------------------
// HANDLE NEGATIVE RESPONSE
// --------------------------------------------------

if (isNegativeResponse) {

    currentPropertyIds.forEach(
        (id) => {

            if (
                !rejectedPropertyIds.includes(id)
            ) {

                rejectedPropertyIds.push(
                    id
                );

            }

        }
    );

}

console.log(
    "REJECTED PROPERTY IDS:",
    rejectedPropertyIds
);


            console.log(
                "REJECTED PROPERTY IDS:",
                rejectedPropertyIds
            );

           
            // --------------------------------------------------
            // SAVE CONVERSATION
            // --------------------------------------------------

            conversationHistory.push({

                role: "user",

                content:
                    text

            });


            conversationHistory.push({

                role: "assistant",

                content:
                    data.response || ""

            });


            // --------------------------------------------------
            // DISPLAY AI RESPONSE
            // --------------------------------------------------

            if (data.response) {

                addTranscript(
                    data.response,
                    "ai"
                );

            }


            // --------------------------------------------------
            // DISPLAY PROPERTY INFORMATION
            // --------------------------------------------------

            if (
                data.properties &&
                data.properties.length > 0
            ) {

                data.properties.forEach(
                    (property) => {

                        let propertyText =
                            `${property.title || "Property"}`;


                        if (property.city) {

                            propertyText +=
                                ` — ${property.city}`;

                        }


                        if (property.price) {

                            propertyText +=
                                ` — ${property.price}`;

                        }


                        addTranscript(
                            propertyText,
                            "property"
                        );

                    }
                );

            }


        } catch (error) {

            console.error(
                "VOICE AI ERROR:",
                error
            );


            addTranscript(
                "Sorry, I could not connect to the AI assistant.",
                "ai"
            );


        } finally {

            isProcessing =
                false;


            // Process the next queued message first.
            processNextAIMessage();


            // If there are no more messages waiting,
            // start listening again.
            if (
                isCalling &&
                !isProcessing &&
                !isRecording
            ) {

                startRecognition();

            }

        }

    }


    // --------------------------------------------------
    // ADD MESSAGE TO AI QUEUE
    // --------------------------------------------------

    function queueAIMessage(text) {

        if (!text || !text.trim()) {
            return;
        }


        aiMessageQueue.push(
            text.trim()
        );


        console.log(
            "AI MESSAGE QUEUE:",
            aiMessageQueue
        );


        processNextAIMessage();


    }


    // --------------------------------------------------
    // PROCESS NEXT QUEUED MESSAGE
    // --------------------------------------------------

    function processNextAIMessage() {

        if (isProcessing) {
            return;
        }


        if (
            aiMessageQueue.length === 0
        ) {

            return;

        }


        const nextMessage =
            aiMessageQueue.shift();


        processAIMessage(
            nextMessage
        );

    }
// --------------------------------------------------
// GEMINI LIVE CONNECTION TEST
// --------------------------------------------------

async function testGeminiLiveConnection() {

    console.log(
        "REQUESTING GEMINI LIVE TOKEN..."
    );

    try {

        const tokenResponse =
            await fetch(
                `/ai/api/gemini-live-token?business_id=${businessId}`
            );

        const tokenData =
            await tokenResponse.json();
        
        console.log(
          "SAVED GREETING RECEIVED FROM BACKEND:",
           tokenData.greeting_message
        );

        console.log(
            "GEMINI TOKEN RESPONSE:",
            tokenData
        );
        console.log(
          "SAVED RESPONSE STYLE:",
           tokenData.response_style
        );

        console.log(
          "SAVED PREFERRED LANGUAGE:",
          tokenData.preferred_language
        );

        if (
            !tokenResponse.ok ||
            !tokenData.success
        ) {

            throw new Error(
                tokenData.message ||
                "Could not get Gemini Live token."
            );
        }

        const token = tokenData.token;

        const geminiGreetingMessage =
            (tokenData.greeting_message || "").trim();

        const geminiBusinessName =
            (tokenData.business_name || "").trim();

        const geminiAssistantIntroduction =
            (tokenData.assistant_introduction || "").trim();

        const geminiVoiceName =
            (tokenData.voice_name || "Kore").trim();


        // --------------------------------------------------
        // GEMINI LIVE WEBSOCKET
        // --------------------------------------------------

        const geminiUrl =
            "wss://generativelanguage.googleapis.com/" +
            "ws/google.ai.generativelanguage.v1beta." +
            "GenerativeService.BidiGenerateContentConstrained" +
            `?access_token=${encodeURIComponent(token)}`;


        console.log(
            "CONNECTING TO GEMINI LIVE..."
        );


        geminiSocket =
            new WebSocket(
                geminiUrl
            );


        // --------------------------------------------------
        // WEBSOCKET OPEN
        // --------------------------------------------------

        geminiSocket.onopen = (event) => {
                console.log(
                    "GEMINI LIVE WEBSOCKET CONNECTED"
                );

                callTitle.textContent =
                    "AI Assistant Connected";

                callStatus.textContent =
                    "Preparing your conversation...";


                const setupMessage = {

                    setup: {

                        model:
                            "models/gemini-3.8-live",


                        generationConfig: {
                            responseModalities: [
                                "AUDIO"
                            ],
                            speechConfig: {
                                voiceConfig: {
                                    prebuiltVoiceConfig: {
                                        voiceName: geminiVoiceName
                                    }
                                }
                            }
                        },


                        inputAudioTranscription: {},


                        outputAudioTranscription: {},


                        tools: [

                            {

                                functionDeclarations: [

                                    {

                                        name:
                                            "search_properties",

                                        behavior:
                                            "BLOCKING",

                                        description:
                                            "Search the real estate property database. Use 'new_search' when the customer gives new or changed property requirements. Use 'next_property' when the customer rejects the currently shown property or asks to see another property.",

                                        parameters: {

                                            type:
                                                "OBJECT",

                                            properties: {

                                                city: {

                                                    type:
                                                        "STRING",

                                                    description:
                                                        "City to search."

                                                },

                                                property_type: {

                                                    type:
                                                        "STRING",

                                                    description:
                                                        "Property type."

                                                },

                                                bedrooms: {

                                                    type:
                                                        "INTEGER",

                                                    description:
                                                        "Number of bedrooms."

                                                },

                                                budget: {

                                                    type:
                                                        "NUMBER",

                                                    description:
                                                        "Maximum budget in Indian rupees."

                                                },

                                                search_mode: {

                                                    type:
                                                        "STRING",

                                                    enum: [
                                                        "new_search",
                                                        "next_property",
                                                        
                                                    ],

                                                    description:
                                                        "Use new_search for new or changed requirements. Use next_property when the customer rejects the currently shown property or asks for another property."

                                                }

                                            },

                                            required: [
                                                "search_mode"
                                            ]

                                        }

                                    },
                                    {

                                        name:
                                            "get_business_information",

                                        behavior:
                                            "BLOCKING",

                                        description:
                                            "Get the verified business profile information from the database when the customer asks about the business, company, services, background, or wants to know more about the business.",

                                        parameters: {

                                            type:
                                                "OBJECT",

                                            properties: {}

                                        }

                                    },

                                    {

                                        name:
                                            "save_customer",

                                        behavior:
                                            "BLOCKING",

                                        description:
                                            "Save a customer to the business CRM after the customer has provided their full name and phone number. Email is optional. If the customer provides an email address, save it. If the customer declines to provide an email or does not have one, continue without it. Never require email to save a customer and never repeatedly ask for email after the customer declines.",

                                        parameters: {

                                            type:
                                                "OBJECT",

                                            properties: {

                                                full_name: {

                                                    type:
                                                        "STRING",

                                                    description:
                                                        "Customer's full name. Required."

                                                },

                                                phone: {

                                                    type:
                                                        "STRING",

                                                    description:
                                                        "Customer's phone number. Required."

                                                },

                                                email: {

                                                    type:
                                                        "STRING",

                                                    description:
                                                        "Customer's email address, only if provided voluntarily. Optional; do not invent an email address."

                                                },

                                                city: {

                                                    type:
                                                        "STRING",

                                                    description:
                                                        "Customer's city, if provided."

                                                }

                                            },

                                            required: [
                                                "full_name",
                                                "phone"
                                            ]

                                        }

                                    },


                                    {

                                        name:
                                            "save_customer_requirement",

                                        behavior:
                                            "BLOCKING",

                                        description:
                                            "Save or update the customer's latest property requirement after the customer has discussed what type of property they want.",

                                        parameters: {

                                            type:
                                                "OBJECT",

                                            properties: {

                                                phone: {

                                                    type:
                                                        "STRING",

                                                    description:
                                                        "Customer's phone number used to identify the customer."

                                                },

                                                property_type: {

                                                    type:
                                                        "STRING",

                                                    description:
                                                        "Property type such as Apartment, Villa, House, Plot, or Commercial."

                                                },

                                                preferred_location: {

                                                    type:
                                                        "STRING",

                                                    description:
                                                        "City or preferred location."

                                                },

                                                min_budget: {

                                                    type:
                                                        "NUMBER",

                                                    description:
                                                        "Minimum budget in Indian rupees, if provided."

                                                },

                                                max_budget: {

                                                    type:
                                                        "NUMBER",

                                                    description:
                                                        "Maximum budget in Indian rupees, if provided."

                                                },

                                                bedrooms: {

                                                    type:
                                                        "INTEGER",

                                                    description:
                                                        "Required number of bedrooms."

                                                },

                                                notes: {

                                                    type:
                                                        "STRING",

                                                    description:
                                                        "Additional customer requirements or preferences."

                                                }

                                            },

                                            required: [
                                                "phone",
                                                "property_type"
                                            ]

                                        }

                                    },
                                    {

                                         name:
                                            "create_lead",

                                        behavior:
                                            "BLOCKING",

                                        description:
                                            "Create or update a CRM lead only after the customer has shown interest in a matching property, provided their full name and phone number, and provided a preferred follow-up date. If the customer does not want to provide a specific follow-up date, use an empty string.",

                                        parameters: {

                                            type:
                                                "OBJECT",

                                            properties: {

                                                phone: {

                                                    type:
                                                        "STRING",

                                                    description:
                                                        "Customer's phone number used to identify the customer."

                                                },

                                                follow_up_date: {

                                                    type:
                                                        "STRING",

                                                    description:
                                                        "Customer's preferred follow-up date in YYYY-MM-DD format. If the customer does not want to specify a date, use an empty string."

                                                },

                                                conversation: {

                                                    type:
                                                        "STRING",

                                                    description:
                                                        "The complete conversation transcript between the customer and the AI assistant."

                                                }

                                            },

                                            required: [
                                                "phone",
                                                "follow_up_date",
                                                "conversation"
                                            ]

                                        }

                                    }

                                ]

                            }

                        ],

                        systemInstruction: {

                            parts: [

                                {


                                    text:


                                       "You are an AI voice assistant " +
                                       "for the real-estate business. " +

                                       "The business you represent is: " +
                                       (geminiBusinessName || "the real-estate business") +
                                       ". " +

                                        (
                                          geminiAssistantIntroduction
                                           ? "Your configured introduction is: " +
                                          geminiAssistantIntroduction +
                                          ". Use it naturally when relevant, without " +
                                          "repeating it unnecessarily. "
                                        : ""
                                        ) +

                                        "Use the initial greeting provided after connection setup. " +
                                        "Speak that greeting once, exactly as provided, without " +
                                        "adding another introduction or repeating the greeting. " +
                                        "After the greeting, continue the conversation naturally " +
                                        "and follow all other instructions. " +


                                        
                                        // ------------------------------------------
                                        // LANGUAGE AND CONVERSATION
                                        // ------------------------------------------

                                        "You are a multilingual voice assistant. " +

                                        // Response style preference
                                        "Use a " +
                                        (
                                            tokenData.response_style === "professional"
                                                ? "professional and formal"
                                                : tokenData.response_style === "concise"
                                                    ? "concise and direct"
                                                    : "friendly and conversational"
                                        ) +
                                        " communication style. " +

                                        // Preferred language preference
                                        (
                                            tokenData.preferred_language === "en"
                                                ? "Always respond in English. "
                                                : tokenData.preferred_language === "te"
                                                    ? "Always respond in Telugu. "
                                                    : tokenData.preferred_language === "hi"
                                                        ? "Always respond in Hindi. "
                                                        : "Automatically identify and understand the customer's language. Respond naturally in the same language. Support language switching and mixed-language speech whenever supported by the active Gemini Live model. Do not force the customer to speak English. "
                                        ) +

                                        "Preserve property titles, prices, locations, names, phone numbers, and database values accurately. " +

                                        "Keep responses clear and polite while following the selected communication style. " +
                                        "Use previous conversation context and reuse " +
                                        "information already provided. Ask only for " +
                                        "missing information. Do not repeatedly ask " +
                                        "the same question after it has been answered. " +

                                        // ------------------------------------------
                                        // BUSINESS INFORMATION
                                        // ------------------------------------------

                                        "When the customer asks about the business, " +
                                        "company, owner, services, or business " +
                                        "background, you MUST call the " +
                                        "get_business_information function. Answer " +
                                        "using only verified information returned by " +
                                        "the function. Never invent missing details. " +

                                        // ------------------------------------------
                                        // PROPERTY SEARCH
                                        // ------------------------------------------

                                        "Whenever the customer asks to find, search, " +
                                        "recommend, or show properties, you MUST call " +
                                        "the search_properties function. Use the latest " +
                                        "known city, property type, bedrooms, and budget. " +
                                        "Reuse previous values when the customer changes " +
                                        "only one requirement. " +

                                        "Use new_search when starting a search or when " +
                                        "the customer changes their requirements. Use " +
                                        "next_property when the customer rejects the " +
                                        "current property or asks to see another without " +
                                        "changing their requirements. " +

                                        "When only the budget changes and the city, " +
                                        "property type, and bedrooms remain the same, " +
                                        "preserve the previously rejected property " +
                                        "exclusions while searching with the updated " +
                                        "budget. When the city, property type, or " +
                                        "bedrooms change, treat it as a different search. " +

                                        "Present one matching property at a time. Use " +
                                        "the exact property title returned by the " +
                                        "database. Provide only verified property " +
                                        "details returned by search_properties. Never " +
                                        "invent listings, prices, availability, " +
                                        "locations, or amenities. " +

                                        "Ask whether the customer is interested in " +
                                        "the property presented. If rejected, offer " +
                                        "another eligible property that has not been " +
                                        "rejected. If no matching properties remain, " +
                                        "explain that and ask whether the customer " +
                                        "wants to change their requirements. Never " +
                                        "claim a property was excluded unless the " +
                                        "search results confirm it. " +

                                        // ------------------------------------------
                                        // CUSTOMER INFORMATION
                                        // ------------------------------------------

                                        "The customer's full name and phone number " +
                                        "are mandatory for saving a customer. When " +
                                        "both are available, call save_customer. Do " +
                                        "not wait for an email address before saving. " +

                                        "Email is optional, but you MUST politely ask for " +
                                        "the customer's email address once after collecting " +
                                        "their full name and phone number. Ask: 'May I have " +
                                        "your email address? You can skip this if you prefer.' " +
                                        "If the customer provides an email, pass it to " +
                                        "save_customer. If the customer declines, skips the " +
                                        "question, or says they do not have an email, continue " +
                                        "without an email and do not ask again. Never invent " +
                                        "an email address. Do not delay saving the customer " +
                                        "while waiting for an optional email. " +

                                        "If the customer provides only their name " +
                                        "or only their phone number, ask for the " +
                                        "missing mandatory information. Do not ask " +
                                        "again for information already provided. " +

                                        // ------------------------------------------
                                        // CUSTOMER REQUIREMENTS
                                        // ------------------------------------------

                                        "When the customer discusses property " +
                                        "requirements, use the latest known property " +
                                        "type, preferred location, budget, bedrooms, " +
                                        "and preferences. Call save_customer_requirement " +
                                        "when its required arguments are available. " +

                                        "If the customer changes their requirements, " +
                                        "update the saved requirement using the latest " +
                                        "values. Do not invent a phone number or " +
                                        "required argument. " +

                                        // ------------------------------------------
                                        // LEAD CREATION AND FOLLOW-UP
                                        // ------------------------------------------

                                        "Do not create a lead merely because the " +
                                        "customer searched for properties or provided " +
                                        "requirements. A matching property must have " +
                                        "been found and the customer must express " +
                                        "interest in it. " +

                                        "Before calling create_lead, make sure " +
                                        "save_customer has succeeded and " +
                                        "save_customer_requirement has succeeded. " +
                                        "The customer's full name and phone number " +
                                        "must be available. " +

                                        "Ask naturally for the customer's preferred " +
                                        "follow-up date. If the customer gives a clear " +
                                        "date, convert it to YYYY-MM-DD. If the date " +
                                        "is ambiguous, ask one brief clarification. " +

                                        "If the customer explicitly declines to " +
                                        "specify a date, use an empty string if " +
                                        "accepted by the create_lead tool. Never " +
                                        "invent a follow-up date. Do not interpret " +
                                        "vague statements such as 'when you are free' " +
                                        "as a confirmed date. " +

                                        "Call create_lead only after the required " +
                                        "conditions are met. Pass the confirmed phone " +
                                        "number, the agreed follow-up date or permitted " +
                                        "empty string, and the complete available " +
                                        "conversation transcript. If a required save " +
                                        "operation fails, do not claim it succeeded " +
                                        "or create a lead as though it succeeded. " +

                                        "After create_lead succeeds, confirm naturally " +
                                        "that the details have been recorded. Never " +
                                        "claim that a customer, requirement, or lead " +
                                        "was saved unless the corresponding tool " +
                                        "confirms success."


                                }

                            ]

                        }
                    
                    }

                };


                console.log(
                    "SENDING GEMINI LIVE SETUP..."
                );
                console.log(
                   "GEMINI SETUP MESSAGE:",
                    JSON.stringify(
                         setupMessage,
                         null,
                         2
                    )
                );


                event.target.send(
                    JSON.stringify(
                        setupMessage
                    )
                );
                

            };


        // --------------------------------------------------
        // WEBSOCKET MESSAGE
        // --------------------------------------------------

geminiSocket.onmessage =
    async (event) => {

        try {

            // ------------------------------------------
            // GEMINI MAY SEND THE WEBSOCKET MESSAGE
            // AS A STRING OR AS A BLOB
            // ------------------------------------------

            let messageText;

            if (
                event.data instanceof Blob
            ) {

                messageText =
                    await event.data.text();

            } else {

                messageText =
                    event.data;

            }


            console.log(
                "GEMINI RAW MESSAGE:",
                messageText
            );


                    const response = 
                        JSON.parse( 
                            messageText 
                        ); 
 
                    console.log( 
                        "GEMINI LIVE RESPONSE:", 
                        response 
                    ); 


                    // --------------------------------------------------
                    // GEMINI TOOL CALL
                    // --------------------------------------------------

                    if (
                        response.toolCall
                    ) {

                        console.log(
                            "GEMINI TOOL CALL RECEIVED:",
                            response.toolCall
                        );

                        const functionResponses = [];

                        for (
                            const functionCall of
                                response.toolCall.functionCalls || []
                        ) {

                            console.log(
                                "GEMINI FUNCTION CALL:",
                                functionCall.name
                            );

                            console.log(
                                "GEMINI FUNCTION ARGUMENTS:",
                                functionCall.args
                            );

                            if (
                                functionCall.name ===
                                "search_properties"
                            ) {

                                try {

                                    const searchMode =
                                        functionCall.args?.search_mode;


                                    if (
                                        searchMode ===
                                        "new_search"
                                    ) {

                                    const previousSearch =
                                        lastPropertySearch || {};

                                    const newSearch = {
                                        city:
                                            functionCall.args?.city ??
                                            previousSearch.city ??
                                            null,

                                        property_type:
                                            functionCall.args?.property_type ??
                                            previousSearch.property_type ??
                                            null,

                                        bedrooms:
                                            functionCall.args?.bedrooms ??
                                            previousSearch.bedrooms ??
                                            null,

                                        budget:
                                            functionCall.args?.budget ??
                                            previousSearch.budget ??
                                            null
                                    };

                                    const normalize = (value) =>
                                        value == null
                                            ? ""
                                            : String(value)
                                                .trim()
                                                .toLowerCase();

                                    const isSameSearch =
                                        lastPropertySearch &&
                                        normalize(newSearch.city) ===
                                            normalize(previousSearch.city) &&
                                        normalize(newSearch.property_type) ===
                                            normalize(previousSearch.property_type) &&
                                        newSearch.bedrooms ===
                                            previousSearch.bedrooms;

                                    if (!isSameSearch) {

                                        excludedPropertyIds = [];

                                    }

                                    currentPropertyId =
                                        null;

                                    lastPropertySearch =
                                        newSearch;


                                    }


                                    if (
                                        searchMode ===
                                        "next_property"
                                    ) {

                                        if (
                                            currentPropertyId &&
                                            !excludedPropertyIds.includes(
                                                currentPropertyId
                                            )
                                        ) {

                                            excludedPropertyIds.push(
                                                currentPropertyId
                                            );

                                        }

                                    }

                                    console.log(
                                        "GEMINI PROPERTY SEARCH REQUEST:",
                                        {
                                            functionArguments:
                                                functionCall.args,

                                            searchMode:
                                                searchMode,

                                            lastPropertySearch:
                                                lastPropertySearch,

                                            currentPropertyId:
                                                currentPropertyId,

                                            excluded_property_ids:
                                                excludedPropertyIds
                                        }
                                    );
                                    
                                    const searchResponse =
                                        await fetch(
                                            "/ai/api/gemini-live/search-properties",
                                            {
                                                method: "POST",
                                                headers: {
                                                    "Content-Type":
                                                        "application/json"
                                                },
                                                body: JSON.stringify({

                                                    business_id:
                                                        businessId,

                                                    city:
                                                        searchMode === "next_property"
                                                            ? lastPropertySearch.city
                                                            : functionCall.args?.city,

                                                    property_type:
                                                        searchMode === "next_property"
                                                            ? null
                                                            : functionCall.args?.property_type,

                                                    bedrooms:
                                                        searchMode === "next_property"
                                                            ? lastPropertySearch.bedrooms
                                                            : functionCall.args?.bedrooms,

                                                    budget:
                                                        searchMode === "next_property"
                                                            ? lastPropertySearch.budget
                                                            : functionCall.args?.budget,
                                                    excluded_property_ids:
                                                        excludedPropertyIds

                                                })
                                            }
                                        );

                                    const searchData =
                                        await searchResponse.json();
                                    console.log("NEXT PROPERTY API RESPONSE:", searchData);
                                    console.log(
                                        "RETURNED PROPERTY IDS:",
                                        (searchData.properties || []).map(
                                            property => ({
                                                id: property.property_id,
                                                title: property.title
                                            })
                                        )
                                    );

                                    if (
                                        searchData.success &&
                                        searchData.properties &&
                                        searchData.properties.length > 0
                                    ) {

                                        const firstProperty =
                                            searchData.properties[0];

                                        searchData.properties = [
                                            firstProperty
                                        ];

                                        currentPropertyId =
                                            firstProperty.property_id;

                                    }

                                    functionResponses.push({
                                        name:
                                            functionCall.name,
                                        id:
                                            functionCall.id,
                                        response: {
                                            result:
                                                searchData
                                        }
                                    });

                                } catch (error) {

                                    console.error(
                                        "GEMINI PROPERTY SEARCH ERROR:",
                                        error
                                    );

                                    functionResponses.push({
                                        name:
                                            functionCall.name,
                                        id:
                                            functionCall.id,
                                        response: {
                                            result: {
                                                success: false,
                                                message:
                                                    "Property search failed."
                                            }
                                        }
                                    });
                                }
                            }

                            else if (
                                functionCall.name ===
                                "get_business_information"
                            ) {

                                try {

                                    const businessResponse =
                                        await fetch(
                                            "/ai/api/gemini-live/business-information",
                                            {
                                                method: "POST",
                                                headers: {
                                                    "Content-Type":
                                                        "application/json"
                                                },
                                                body: JSON.stringify({
                                                    business_id:
                                                        businessId
                                                })
                                            }
                                        );

                                    const businessData =
                                        await businessResponse.json();

                                    console.log(
                                        "GEMINI BUSINESS INFORMATION RESULT:",
                                        businessData
                                    );

                                    functionResponses.push({
                                        name:
                                            functionCall.name,
                                        id:
                                            functionCall.id,
                                        response: {
                                            result:
                                                businessData
                                        }
                                    });

                                } catch (error) {

                                    console.error(
                                        "GEMINI BUSINESS INFORMATION ERROR:",
                                        error
                                    );

                                    functionResponses.push({
                                        name:
                                            functionCall.name,
                                        id:
                                            functionCall.id,
                                        response: {
                                            result: {
                                                success: false,
                                                message:
                                                    "Business information could not be retrieved."
                                            }
                                        }
                                    });
                                }
                            }

                            else if (
                                functionCall.name ===
                                "save_customer"
                            ) {

                                try {


                                    const saveResponse =
                                        await fetch(
                                            "/ai/api/gemini-live/save-customer",
                                            {
                                                method: "POST",
                                                headers: {
                                                    "Content-Type":
                                                        "application/json"
                                                },
                                                body: JSON.stringify({
                                                    business_id:
                                                        businessId,
                                                    full_name:
                                                        functionCall.args?.full_name,
                                                    phone:
                                                        functionCall.args?.phone,
                                                    email:
                                                        functionCall.args?.email,
                                                    city:
                                                        functionCall.args?.city
                                                })
                                            }
                                        );
                                        

                                    const saveData =
                                        await saveResponse.json();

                                    if (
                                        saveResponse.ok &&
                                        saveData.success &&
                                        saveData.customer?.id
                                    ) {
                                        savedCustomerId = Number(
                                            saveData.customer.id
                                        );

                                        console.log(
                                            "SAVED CUSTOMER ID FOR CONVERSATION:",
                                            savedCustomerId
                                        );
                                    }

                                    console.log(
                                        "GEMINI CUSTOMER SAVE RESULT:",
                                        saveData
                                    );

                                    functionResponses.push({
                                        name:
                                            functionCall.name,
                                        id:
                                            functionCall.id,
                                        response: {
                                            result:
                                                saveData
                                        }
                                    });

                                } catch (error) {

                                    console.error(
                                        "GEMINI CUSTOMER SAVE ERROR:",
                                        error
                                    );

                                    functionResponses.push({
                                        name:
                                            functionCall.name,
                                        id:
                                            functionCall.id,
                                        response: {
                                            result: {
                                                success: false,
                                                message:
                                                    "Customer save failed."
                                            }
                                        }
                                    });
                                }
                            }

                            else if (
                                functionCall.name ===
                                "save_customer_requirement"
                            ) {

                                try {

                                    const requirementResponse =
                                        await fetch(
                                            "/ai/api/gemini-live/save-customer-requirement",
                                            {
                                                method: "POST",
                                                headers: {
                                                    "Content-Type":
                                                        "application/json"
                                                },
                                                body: JSON.stringify({
                                                    business_id:
                                                        businessId,
                                                    phone:
                                                        functionCall.args?.phone,
                                                    property_type:
                                                        functionCall.args?.property_type,
                                                    preferred_location:
                                                        functionCall.args?.preferred_location,
                                                    min_budget:
                                                        functionCall.args?.min_budget,
                                                    max_budget:
                                                        functionCall.args?.max_budget,
                                                    bedrooms:
                                                        functionCall.args?.bedrooms,
                                                    notes:
                                                        functionCall.args?.notes
                                                })
                                            }
                                        );

                                    const requirementData =
                                        await requirementResponse.json();

                                    console.log(
                                        "GEMINI CUSTOMER REQUIREMENT RESULT:",
                                        requirementData
                                    );

                                    functionResponses.push({
                                        name:
                                            functionCall.name,
                                        id:
                                            functionCall.id,
                                        response: {
                                            result:
                                                requirementData
                                        }
                                    });

                                } catch (error) {

                                    console.error(
                                        "GEMINI CUSTOMER REQUIREMENT ERROR:",
                                        error
                                    );

                                    functionResponses.push({
                                        name:
                                            functionCall.name,
                                        id:
                                            functionCall.id,
                                        response: {
                                            result: {
                                                success: false,
                                                message:
                                                    "Customer requirement save failed."
                                            }
                                        }
                                    });
                                }
                            }
                            else if (
                                functionCall.name ===
                                "create_lead"
                            ) {

                                try {
                                    console.log(
                                       "GEMINI FULL CONVERSATION TRANSCRIPT:",
                                        geminiConversationTranscript
                                    );

                                    const leadResponse =
                                        await fetch(
                                            "/ai/api/gemini-live/create-lead",
                                            {
                                                method: "POST",

                                                headers: {
                                                    "Content-Type":
                                                        "application/json"
                                                },

                                                body: JSON.stringify({

                                                    business_id:
                                                        businessId,

                                                    phone:
                                                        functionCall.args?.phone,

                                                    follow_up_date:
                                                        functionCall.args?.follow_up_date,

                                                    conversation:
                                                        geminiConversationTranscript

                                                })
                                            }
                                        );

                                    const leadData =
                                        await leadResponse.json();

                                    console.log(
                                        "GEMINI LEAD CREATION RESULT:",
                                        leadData
                                    );

                                    functionResponses.push({

                                        name:
                                            functionCall.name,

                                        id:
                                            functionCall.id,

                                        response: {

                                            result:
                                                leadData

                                        }

                                    });

                                } catch (error) {

                                    console.error(
                                        "GEMINI LEAD CREATION ERROR:",
                                        error
                                    );

                                    functionResponses.push({

                                        name:
                                            functionCall.name,

                                        id:
                                            functionCall.id,

                                        response: {

                                            result: {

                                                success: false,

                                                message:
                                                    "Lead creation failed."

                                            }

                                        }

                                    });

                                }

                            }                            


                        }

                        if (
                            geminiSocket &&
                            geminiSocket.readyState ===
                                WebSocket.OPEN
                        ) {

                            geminiSocket.send(
                                JSON.stringify({
                                    toolResponse: {
                                        functionResponses:
                                            functionResponses
                                    }
                                })
                            );

                            console.log(
                                "GEMINI TOOL RESPONSE SENT:",
                                functionResponses
                            );
                        }
                        
                        
                    }
                    // ------------------------------------------ 
                    // SETUP COMPLETE 
                    // ------------------------------------------ 
 
                    if ( 
                        response.setupComplete 
                    ) { 

                        console.log( 
                            "GEMINI LIVE SETUP COMPLETE" 
                        ); 

                        geminiSetupComplete = 
                            true; 

                        callTitle.textContent = 
                            "AI Voice Assistant";

                        callStatus.textContent = 
                            "Preparing your greeting..."; 

                        
                        // Request the AI's first spoken greeting.
                        if (
                            geminiSocket &&
                            geminiSocket.readyState === WebSocket.OPEN
                        ) {
                            geminiSocket.send(
                                JSON.stringify({
                                    clientContent: {
                                        turns: [
                                            {
                                                role: "user",
                                                parts: [
                                                    {
                                                        text: geminiGreetingMessage
                                                            ? "Speak this exact greeting to the customer once, without adding another introduction: " + geminiGreetingMessage
                                                            : "Begin the conversation now. Greet the customer naturally as the AI assistant for this real-estate business, and ask how you can help with their property requirements. Follow your system instructions and do not invent the business name."
                                                    }
                                                ]
                                            }
                                        ],
                                        turnComplete: true
                                    }
                                })
                            );

                            console.log(
                                "INITIAL GREETING REQUEST SENT"
                            );
                        }

                        startGeminiMicrophone();

                    }

                    // ------------------------------------------
                    // SERVER CONTENT
                    // ------------------------------------------

                    if (
                        response.serverContent
                    ) {

                        const serverContent =
                            response.serverContent;


                        // --------------------------------------
                        // GEMINI INPUT TRANSCRIPTION
                        // --------------------------------------

                        if (
                            serverContent.inputTranscription
                        ) {

                            const text =
                                serverContent
                                    .inputTranscription
                                    .text || "";


                            if (
                                text.trim()
                            ) {

                                console.log(
                                    "GEMINI INPUT:",
                                    text
                                );


                                addTranscript(
                                    text,
                                    "customer"
                                );


                                geminiInputTranscript +=
                                    text;

                            }

                        }
                        // --------------------------------------
                        // GEMINI OUTPUT TRANSCRIPTION
                        // --------------------------------------

                        if (
                            serverContent.outputTranscription
                        ) {

                            const text =
                                serverContent
                                    .outputTranscription
                                    .text || "";


                            if (
                                text.trim()
                            ) {

                                console.log(
                                    "GEMINI OUTPUT:",
                                    text
                                );


                                geminiOutputTranscript +=
                                    text;
                            }

                        }

                        // --------------------------------------
                        // GEMINI AUDIO
                        // --------------------------------------

                        if (
                            serverContent.modelTurn &&
                            serverContent.modelTurn.parts
                        ) {

                            for (
                                const part
                                of serverContent.modelTurn.parts
                            ) {

                                if (
                                    part.inlineData &&
                                    part.inlineData.data
                                ) {

                                    console.log(
                                        "GEMINI AUDIO RECEIVED:",
                                        part.inlineData.data.length,
                                        "base64 characters"
                                    );


                                    callStatus.textContent =
                                        "AI is speaking...";


                                    playGeminiAudio(
                                        part.inlineData.data
                                    );

                                }

                            }

                        }


                        // --------------------------------------
                        // GENERATION COMPLETE
                        // --------------------------------------

                        if (
                            serverContent.generationComplete
                        ) {

                            console.log(
                                "GEMINI GENERATION COMPLETE"
                            );

                        }


                        // ------------------------------------------
                        // TURN COMPLETE
                        // ------------------------------------------

                        if (
                            serverContent.turnComplete
                        ) {

                            console.log(
                                "GEMINI TURN COMPLETE"
                            );


                            if (
                                geminiInputTranscript.trim()
                            ) {

                                geminiConversationTranscript +=
                                    "Customer: " +
                                    geminiInputTranscript.trim() +
                                    "\n";

                                geminiInputTranscript =
                                    "";

                            }


                            if (
                                geminiOutputTranscript.trim()
                            ) {

                                addTranscript(
                                    geminiOutputTranscript.trim(),
                                    "ai"
                                );

                                geminiConversationTranscript +=
                                    "AI: " +
                                    geminiOutputTranscript.trim() +
                                    "\n";

                                geminiOutputTranscript =
                                    "";

                            }


                            callStatus.textContent =
                                "Listening... Speak now.";

                        }
                    }


                } catch (error) {

                    console.error(
                        "GEMINI MESSAGE PARSE ERROR:",
                        error
                    );

                }

            };
        // --------------------------------------------------
        // WEBSOCKET ERROR
        // --------------------------------------------------

        geminiSocket.onerror =
            (error) => {

                console.error(
                    "GEMINI LIVE WEBSOCKET ERROR:",
                    error
                );

                callStatus.textContent =
                    "Gemini Live connection failed.";

            };


        // --------------------------------------------------
        // WEBSOCKET CLOSE
        // --------------------------------------------------

        geminiSocket.onclose =
            (event) => {

                console.log(
                    "GEMINI LIVE WEBSOCKET CLOSED:",
                    event.code,
                    event.reason
                );

                geminiSetupComplete =
                    false;

                geminiSocket =
                    null;

            };


    } catch (error) {

        console.error(
            "GEMINI LIVE CONNECTION ERROR:",
            error
        );

        callStatus.textContent =
            "Could not connect to Gemini Live.";

        addTranscript(
            "Could not connect to Gemini Live.",
            "ai"
        );

    }

}

// --------------------------------------------------
// START GEMINI LIVE MICROPHONE
// --------------------------------------------------

async function startGeminiMicrophone() {

    if (
        !geminiSocket ||
        geminiSocket.readyState !== WebSocket.OPEN
    ) {

        console.error(
            "GEMINI MICROPHONE ERROR: SOCKET NOT OPEN"
        );

        return;

    }

    if (!geminiSetupComplete) {

        console.error(
            "GEMINI MICROPHONE ERROR: SETUP NOT COMPLETE"
        );

        return;

    }

    if (geminiMicrophoneActive) {

        console.log(
            "GEMINI MICROPHONE ALREADY ACTIVE"
        );

        return;

    }

    try {

        console.log(
            "REQUESTING GEMINI MICROPHONE..."
        );

        geminiMicStream =
            await navigator.mediaDevices.getUserMedia({

                audio: {

                    channelCount: 1,

                    echoCancellation: true,

                    noiseSuppression: true,

                    autoGainControl: true

                }

            });


        console.log(
            "GEMINI MICROPHONE ACCESS GRANTED"
        );


        // --------------------------------------------------
        // CREATE AUDIO CONTEXT
        // --------------------------------------------------

        geminiMicAudioContext =
            new (
                window.AudioContext ||
                window.webkitAudioContext
            )({

                sampleRate: 16000

            });


        if (
            geminiMicAudioContext.state ===
            "suspended"
        ) {

            await geminiMicAudioContext.resume();

        }


        // --------------------------------------------------
        // CREATE MICROPHONE SOURCE
        // --------------------------------------------------

        geminiMicSource =
            geminiMicAudioContext
                .createMediaStreamSource(
                    geminiMicStream
                );


        // --------------------------------------------------
        // CREATE PCM PROCESSOR
        // --------------------------------------------------

        geminiMicProcessor =
            geminiMicAudioContext
                .createScriptProcessor(
                    4096,
                    1,
                    1
                );


        geminiMicProcessor.onaudioprocess =
            (event) => {

                if (
                    !geminiSocket ||
                    geminiSocket.readyState !==
                        WebSocket.OPEN
                ) {

                    return;

                }


                if (!geminiSetupComplete) {

                    return;

                }


                const inputData =
                    event.inputBuffer
                        .getChannelData(0);


                // ------------------------------------------
                // FLOAT32 → 16-BIT PCM
                // ------------------------------------------

                const pcmData =
                    new Int16Array(
                        inputData.length
                    );


                for (
                    let i = 0;
                    i < inputData.length;
                    i++
                ) {

                    let sample =
                        Math.max(
                            -1,
                            Math.min(
                                1,
                                inputData[i]
                            )
                        );


                    pcmData[i] =
                        sample < 0
                            ? sample * 32768
                            : sample * 32767;

                }


                // ------------------------------------------
                // SEND RAW PCM TO GEMINI LIVE
                // ------------------------------------------

                const base64Audio =
                    int16ToBase64(
                        pcmData
                    );


                geminiSocket.send(
                    JSON.stringify({

                        realtimeInput: {

                            audio: {

                                mimeType:
                                    "audio/pcm;rate=16000",

                                data:
                                    base64Audio

                            }

                        }

                    })
                );

            };


        // --------------------------------------------------
        // CONNECT AUDIO NODES
        // --------------------------------------------------

        geminiMicSource.connect(
            geminiMicProcessor
        );


        geminiMicProcessor.connect(
            geminiMicAudioContext.destination
        );


        geminiMicrophoneActive =
            true;


        isRecording =
            true;


        callOrb.classList.add(
            "listening"
        );


        callStatus.textContent =
            "Listening... Speak now.";


        console.log(
            "GEMINI MICROPHONE STARTED"
        );


    } catch (error) {

        console.error(
            "GEMINI MICROPHONE ERROR:",
            error
        );


        geminiMicrophoneActive =
            false;


        isRecording =
            false;


        callOrb.classList.remove(
            "listening"
        );


        if (
            error.name ===
            "NotAllowedError"
        ) {

            callStatus.textContent =
                "Microphone permission was denied.";

        } else {

            callStatus.textContent =
                "Could not access the microphone.";

        }

    }

}


// --------------------------------------------------
// CONVERT INT16 PCM → BASE64
// --------------------------------------------------

function int16ToBase64(
    pcmData
) {

    const bytes =
        new Uint8Array(
            pcmData.buffer
        );


    let binary = "";


    const chunkSize =
        0x8000;


    for (
        let i = 0;
        i < bytes.length;
        i += chunkSize
    ) {

        const chunk =
            bytes.subarray(
                i,
                Math.min(
                    i + chunkSize,
                    bytes.length
                )
            );


        binary +=
            String.fromCharCode(
                ...chunk
            );

    }


    return btoa(
        binary
    );

}
// --------------------------------------------------
// STOP GEMINI LIVE MICROPHONE
// --------------------------------------------------

function stopGeminiMicrophone() {

    console.log(
        "STOPPING GEMINI LIVE MICROPHONE..."
    );


    geminiMicrophoneActive =
        false;


    // --------------------------------------------------
    // STOP MICROPHONE STREAM
    // --------------------------------------------------

    if (geminiMicStream) {

        geminiMicStream
            .getTracks()
            .forEach(
                (track) => track.stop()
            );

        geminiMicStream =
            null;

    }


    // --------------------------------------------------
    // DISCONNECT MICROPHONE AUDIO NODES
    // --------------------------------------------------

    if (geminiMicProcessor) {

        geminiMicProcessor.disconnect();

        geminiMicProcessor =
            null;

    }


    if (geminiMicSource) {

        geminiMicSource.disconnect();

        geminiMicSource =
            null;

    }


    // --------------------------------------------------
    // CLOSE MICROPHONE AUDIO CONTEXT
    // --------------------------------------------------

    if (geminiMicAudioContext) {

        if (
            geminiMicAudioContext.state !==
            "closed"
        ) {

            geminiMicAudioContext.close();

        }

        geminiMicAudioContext =
            null;

    }


    isRecording =
        false;


    callOrb.classList.remove(
        "listening"
    );


    console.log(
        "GEMINI LIVE MICROPHONE STOPPED"
    );

}
// --------------------------------------------------
// PLAY GEMINI LIVE AUDIO
// --------------------------------------------------

function playGeminiAudio(
    base64Audio
) {

    try {

        if (!geminiAudioContext) {

            geminiAudioContext =
                new (
                    window.AudioContext ||
                    window.webkitAudioContext
                )();

        }


        if (
            geminiAudioContext.state ===
            "suspended"
        ) {

            geminiAudioContext.resume();

        }


        // ----------------------------------------------
        // BASE64 → BINARY
        // ----------------------------------------------

        const binaryString =
            atob(base64Audio);

        const byteLength =
            binaryString.length;

        const bytes =
            new Uint8Array(
                byteLength
            );


        for (
            let i = 0;
            i < byteLength;
            i++
        ) {

            bytes[i] =
                binaryString.charCodeAt(i);

        }


        // ----------------------------------------------
        // 16-BIT PCM → FLOAT32
        // GEMINI LIVE OUTPUT = 24kHz
        // ----------------------------------------------

        const sampleCount =
            Math.floor(
                bytes.length / 2
            );


        const floatSamples =
            new Float32Array(
                sampleCount
            );


        const dataView =
            new DataView(
                bytes.buffer
            );


        for (
            let i = 0;
            i < sampleCount;
            i++
        ) {

            const sample =
                dataView.getInt16(
                    i * 2,
                    true
                );


            floatSamples[i] =
                sample / 32768;

        }


        // ----------------------------------------------
        // CREATE AUDIO BUFFER
        // ----------------------------------------------

        const audioBuffer =
            geminiAudioContext.createBuffer(
                1,
                floatSamples.length,
                24000
            );


        audioBuffer
            .getChannelData(0)
            .set(floatSamples);


        // ----------------------------------------------
        // PLAY AUDIO
        // ----------------------------------------------

        const source =
            geminiAudioContext
                .createBufferSource();


        source.buffer =
            audioBuffer;


        source.connect(
            geminiAudioContext.destination
        );


        const currentTime =
            geminiAudioContext.currentTime;


        const startTime =
            Math.max(
                currentTime,
                geminiPlaybackTime
            );


        source.start(
            startTime
        );


        geminiPlaybackTime =
            startTime +
            audioBuffer.duration;


        console.log(
            "GEMINI AUDIO PLAYING:",
            audioBuffer.duration.toFixed(2),
            "seconds"
        );


    } catch (error) {

        console.error(
            "GEMINI AUDIO PLAYBACK ERROR:",
            error
        );

    }

}

async function testDeepgramConnection() {

    console.log("REQUESTING DEEPGRAM TOKEN...");

    try {

        const response = await fetch(
            "/ai/api/deepgram-token"
        );

        const data = await response.json();
         
        console.log(
            "DEEPGRAM TOKEN RESPONSE:",
            data
        );

        if (!response.ok || !data.success) {

            throw new Error(
                data.message ||
                "Could not get Deepgram token."
            );
        }

        const token = data.token;

        console.log(
            "DEEPGRAM TOKEN RECEIVED"
        );

        const deepgramUrl =
            "wss://api.deepgram.com/v1/listen" +
            "?model=nova-3" +
            "&language=en-IN" +
            "&smart_format=true" +
            "&interim_results=true" +
            "&endpointing=300" +
            "&utterance_end_ms=1000" +
            "&vad_events=true" +
            "&numerals=true" +
            "&keyterm=BHK" +
            "&keyterm=Apartment" +
            "&keyterm=Villa" +
            "&keyterm=House" +
            "&keyterm=Plot" +
            "&keyterm=Commercial" +
            "&keyterm=Hyderabad" +
            "&keyterm=Guntur" +
            "&keyterm=Vijayawada" +
            "&keyterm=Kondapur" +
            "&keyterm=bedroom" +
            "&keyterm=bedrooms" +
            "&keyterm=lakhs" +
            "&keyterm=crore";

        console.log(
            "CONNECTING TO DEEPGRAM..."
        );

        deepgramSocket = new WebSocket(
            deepgramUrl,
            ["bearer", token]
        );

        deepgramSocket.onopen = async () => {

            console.log(
                "DEEPGRAM WEBSOCKET CONNECTED"
            );

    deepgramKeepAliveTimer = setInterval(() => {

        if (
            deepgramSocket &&
            deepgramSocket.readyState === WebSocket.OPEN
        ) {

            deepgramSocket.send(
                JSON.stringify({
                    type: "KeepAlive"
                })
            );

            console.log(
                "DEEPGRAM KEEPALIVE SENT"
            );
        }

    }, 8000);

    callStatus.textContent =
        "Deepgram connected. Starting microphone...";

    addTranscript(
        "Deepgram realtime connection established.",
        "ai"
    );

    try {

                const stream =
                    await navigator.mediaDevices.getUserMedia({
                        audio: {
                            channelCount: 1,
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: true
                        }
                    });

                console.log(
                    "MICROPHONE ACCESS GRANTED"
                );

                mediaRecorder = new MediaRecorder(
                    stream,
                    {
                        mimeType: "audio/webm;codecs=opus"
                    }
                );

                isRecording = true;

                callStatus.textContent =
                    "Listening... Speak now.";

                callOrb.classList.add("listening");

                mediaRecorder.onstart = () => {

                    console.log(
                        "DEEPGRAM AUDIO RECORDING STARTED"
                    );
                };

                mediaRecorder.ondataavailable = (
                    event
                ) => {

                    if (
                        event.data &&
                        event.data.size > 0 &&
                        deepgramSocket &&
                        deepgramSocket.readyState === WebSocket.OPEN
                    ) {

                        console.log(
                            "SENDING AUDIO CHUNK:",
                            event.data.size,
                            "bytes"
                        );

                        deepgramSocket.send(
                            event.data
                        );
                    }
                };

                mediaRecorder.onerror = (
                    event
                ) => {

                    console.error(
                        "MEDIA RECORDER ERROR:",
                        event.error
                    );
                };

                mediaRecorder.onstop = () => {

                    console.log(
                        "DEEPGRAM AUDIO RECORDING STOPPED"
                    );

                    isRecording = false;

                    callOrb.classList.remove(
                        "listening"
                    );

                    stream
                        .getTracks()
                        .forEach(
                            (track) => track.stop()
                        );
                };

                mediaRecorder.start(250);

                console.log(
                    "DEEPGRAM MICROPHONE STREAM STARTED"
                );

            } catch (error) {

                console.error(
                    "MICROPHONE ERROR:",
                    error
                );

                callStatus.textContent =
                    "Could not access the microphone.";

                if (
                    error.name ===
                    "NotAllowedError"
                ) {

                    callStatus.textContent =
                        "Microphone permission was denied.";

                }
            }
        };


        deepgramSocket.onmessage = (
            event
        ) => {

            console.log(
                "DEEPGRAM MESSAGE:",
                event.data
            );

            try {

                const data =
                    JSON.parse(event.data);

                console.log(
                    "DEEPGRAM EVENT:",
                    data.type
                );

                if (
                    data.type ===
                    "Results"
                ) {

                    const transcript =
                        data.channel
                            ?.alternatives?.[0]
                            ?.transcript || "";

                    if (!transcript.trim()) {
                        return;
                    }

                    const isFinal =
                        data.is_final === true;

                    console.log(
                        isFinal
                            ? "FINAL TRANSCRIPT:"
                            : "INTERIM TRANSCRIPT:",
                        transcript
                    );

                    showLiveSpeech(
                        transcript
                    );

                    if (isFinal) {

    removeLiveSpeech();

    if (!transcript.trim()) {
        return;
    }

    pendingDeepgramTranscript =
        pendingDeepgramTranscript
            ? pendingDeepgramTranscript + " " + transcript.trim()
            : transcript.trim();

    console.log(
        "DEEPGRAM FINAL PIECE:",
        transcript
    );

    console.log(
        "PENDING COMPLETE UTTERANCE:",
        pendingDeepgramTranscript
    );
}
                }

                if (
                    data.type ===
                    "SpeechStarted"
                ) {

                    console.log(
                        "DEEPGRAM SPEECH STARTED"
                    );

                    callStatus.textContent =
                        "Listening...";
                }

                if (
    data.type ===
    "UtteranceEnd"
) {

    console.log(
        "DEEPGRAM UTTERANCE END"
    );

    callStatus.textContent =
        "Processing...";
        
    const completeTranscript =
        pendingDeepgramTranscript.trim();

    pendingDeepgramTranscript = "";

    if (!completeTranscript) {
        return;
    }

    console.log(
        "COMPLETE DEEPGRAM UTTERANCE:",
        completeTranscript
    );

    addTranscript(
        completeTranscript,
        "customer"
    );

    if (isProcessing) {

        console.log(
            "IGNORING COMPLETE UTTERANCE WHILE AI IS PROCESSING:",
            completeTranscript
        );

        return;
    }

    queueAIMessage(
        completeTranscript
    );
}

            } catch (error) {

                console.error(
                    "DEEPGRAM MESSAGE PARSE ERROR:",
                    error
                );
            }
        };

        deepgramSocket.onerror = (
            error
        ) => {

            console.error(
                "DEEPGRAM WEBSOCKET ERROR:",
                error
            );

            callStatus.textContent =
                "Deepgram connection failed.";
        };

        deepgramSocket.onclose = (
            event
        ) => {

            console.log(
                "DEEPGRAM WEBSOCKET CLOSED:",
                event.code,
                event.reason
            );
            if (deepgramKeepAliveTimer) {

    clearInterval(
        deepgramKeepAliveTimer
    );

    deepgramKeepAliveTimer = null;

    console.log(
        "DEEPGRAM KEEPALIVE TIMER CLEARED"
    );
}

            if (mediaRecorder) {

                if (
                    mediaRecorder.state ===
                    "recording"
                ) {

                    mediaRecorder.stop();
                }

                mediaRecorder = null;
            }

            isRecording = false;

            callOrb.classList.remove(
                "listening"
            );

            deepgramSocket = null;
        };

    } catch (error) {

        console.error(
            "DEEPGRAM CONNECTION ERROR:",
            error
        );

        callStatus.textContent =
            "Could not connect to Deepgram.";
    }
}
// --------------------------------------------------
// START MICROPHONE RECORDING
// --------------------------------------------------

async function startRecognition() {

    if (!isCalling) {
        return;
    }

    if (isRecording) {
        return;
    }

    try {

        console.log(
            "REQUESTING MICROPHONE..."
        );

        const stream =
            await navigator.mediaDevices.getUserMedia({
                audio: true
            });

        console.log(
            "MICROPHONE ACCESS GRANTED"
        );

        audioChunks = [];

        mediaRecorder =
            new MediaRecorder(
                stream,
                {
                    mimeType: "audio/webm"
                }
            );

        isRecording = true;

        callStatus.textContent =
            "Listening... Speak now.";

        callOrb.classList.add(
            "listening"
        );
        

        mediaRecorder.onstart =
            () => {

                console.log(
                    "AUDIO RECORDING STARTED"
                );

            };

        mediaRecorder.ondataavailable =
            (event) => {

                if (
                    event.data &&
                    event.data.size > 0
                ) {

                    audioChunks.push(
                        event.data
                    );

                }

            };

        mediaRecorder.onstop =
            async () => {

                console.log(
                    "AUDIO RECORDING STOPPED"
                );

                isRecording = false;

                callOrb.classList.remove(
                    "listening"
                );

                stream.getTracks().forEach(
                    (track) => track.stop()
                );

                if (
                    audioChunks.length === 0
                ) {

                    console.log(
                        "NO AUDIO RECORDED"
                    );

                    if (
                        isCalling &&
                        !isProcessing
                    ) {

                        startRecognition();

                    }

                    return;

                }

                const audioBlob =
                    new Blob(
                        audioChunks,
                        {
                            type: "audio/webm"
                        }
                    );

                await transcribeRecordedAudio(
                    audioBlob
                );

            };

        mediaRecorder.start();


        // --------------------------------------------------
        // DETECT SPEECH AND SILENCE
        // --------------------------------------------------

        const audioContext =
            new (
                window.AudioContext ||
                window.webkitAudioContext
            )();

        const source =
            audioContext.createMediaStreamSource(
                stream
            );

        const analyser =
            audioContext.createAnalyser();

        analyser.fftSize = 2048;

        source.connect(analyser);

        const dataArray =
            new Uint8Array(
                analyser.fftSize
            );

        let speechDetected = false;
        let silenceStart = null;

        const silenceDuration = 700;
        const speechThreshold = 18;
        const maximumRecordingTime = 10000;

        const recordingStartedAt =
            Date.now();


        function detectSpeech() {

            if (
                !mediaRecorder ||
                mediaRecorder.state !== "recording"
            ) {

                return;

            }


            analyser.getByteTimeDomainData(
                dataArray
            );

            let sum = 0;


            for (
                let i = 0;
                i < dataArray.length;
                i++
            ) {

                const value =
                    dataArray[i] - 128;

                sum += value * value;

            }


            const volume =
                Math.sqrt(
                    sum / dataArray.length
                );


            // ----------------------------------------------
            // CUSTOMER IS SPEAKING
            // ----------------------------------------------

            if (volume > speechThreshold) {

                if (!speechDetected) {

                    speechDetected = true;

                    console.log(
                        "SPEECH DETECTED"
                    );

                }

                silenceStart = null;

            }


            // ----------------------------------------------
            // CUSTOMER STOPPED SPEAKING
            // ----------------------------------------------

            if (
                speechDetected &&
                volume <= speechThreshold
            ) {

                if (!silenceStart) {

                    silenceStart =
                        Date.now();

                }


                if (
                    Date.now() -
                    silenceStart >=
                    silenceDuration
                ) {

                    console.log(
                        "SPEECH ENDED - STOPPING RECORDING"
                    );


                    audioContext.close();


                    if (
                        mediaRecorder &&
                        mediaRecorder.state === "recording"
                    ) {

                        mediaRecorder.stop();

                    }

                    return;

                }

            }


            // ----------------------------------------------
            // MAXIMUM RECORDING TIME
            // ----------------------------------------------

            if (
                Date.now() -
                recordingStartedAt >=
                maximumRecordingTime
            ) {

                console.log(
                    "MAXIMUM RECORDING TIME REACHED"
                );


                audioContext.close();


                if (
                    mediaRecorder &&
                    mediaRecorder.state === "recording"
                ) {

                    mediaRecorder.stop();

                }

                return;

            }


            requestAnimationFrame(
                detectSpeech
            );

        }


        detectSpeech();

    } catch (error) {

        console.error(
            "MICROPHONE ERROR:",
            error
        );

        isRecording = false;

        callOrb.classList.remove(
            "listening"
        );

        if (
            error.name ===
            "NotAllowedError"
        ) {

            callStatus.textContent =
                "Microphone permission was denied.";

        } else {

            callStatus.textContent =
                "Could not access the microphone.";

        }

    }

}
// --------------------------------------------------
// SEND RECORDED AUDIO TO WHISPER
// --------------------------------------------------

async function transcribeRecordedAudio(
    audioBlob
) {

    if (!isCalling) {
        return;
    }

    callStatus.textContent =
        "Transcribing...";

    try {

        console.log(
            "SENDING AUDIO TO WHISPER..."
        );

        const formData =
            new FormData();

        formData.append(
            "audio",
            audioBlob,
            "voice.webm"
        );

        const response =
            await fetch(
                "/ai/api/transcribe",
                {
                    method: "POST",
                    body: formData
                }
            );

        const rawText =
            await response.text();

        console.log(
            "WHISPER STATUS:",
            response.status
        );

        console.log(
            "WHISPER RESPONSE:",
            rawText
        );

        let data;

        try {

            data =
                JSON.parse(rawText);

        } catch (error) {

            throw new Error(
                "Whisper server returned invalid JSON."
            );

        }

        if (
            !response.ok ||
            data.success === false
        ) {

            throw new Error(
                data.message ||
                "Whisper transcription failed."
            );

        }

        const transcript =
            (
                data.transcript ||
                ""
            ).trim();

        console.log(
            "WHISPER TRANSCRIPT:",
            transcript
        );

                if (!transcript) {

            console.log(
                "NO SPEECH DETECTED - LISTENING AGAIN"
            );

            if (
                isCalling &&
                !isProcessing &&
                !isRecording
            ) {

                setTimeout(
                    () => {
                        startRecognition();
                    },
                    300
                );

            }

            return;

        }


        // ----------------------------------------------
        // IGNORE VERY SHORT / INVALID TRANSCRIPTS
        // ----------------------------------------------

        const cleanedTranscript =
            transcript
                .replace(
                    /[.,!?;:]+/g,
                    " "
                )
                .replace(
                    /\s+/g,
                    " "
                )
                .trim();


        const onlyNumbers =
            /^[\d\s,.-]+$/.test(
                cleanedTranscript
            );


        const onlyPunctuation =
            cleanedTranscript.length === 0;


        if (
            onlyPunctuation ||
            onlyNumbers ||
            cleanedTranscript.length < 2
        ) {

            console.log(
                "IGNORING INVALID TRANSCRIPT:",
                transcript
            );

            if (
                isCalling &&
                !isProcessing &&
                !isRecording
            ) {

                setTimeout(
                    () => {
                        startRecognition();
                    },
                    300
                );

            }

            return;

        }

        // ----------------------------------------------
        // DISPLAY CUSTOMER SPEECH
        // ----------------------------------------------

        addTranscript(
            cleanedTranscript,
            "customer"
        );

        console.log(
            "CUSTOMER SAID:",
            cleanedTranscript
        );


        // ----------------------------------------------
        // SEND CUSTOMER MESSAGE ONCE
        // ----------------------------------------------

        if (
            !isProcessing &&
            aiMessageQueue.length === 0
        ) {

            queueAIMessage(
                cleanedTranscript
            );

        }
        

    } catch (error) {

        console.error(
            "WHISPER ERROR:",
            error
        );

        addTranscript(
            "Sorry, I could not understand your voice.",
            "ai"
        );

        callStatus.textContent =
            "Could not transcribe your speech.";

        if (
            isCalling &&
            !isProcessing
        ) {

            startRecognition();

        }

    }

}

   // --------------------------------------------------
    // START CALL
    // --------------------------------------------------

 startBtn.addEventListener("click", () => {

    if (isCalling) return;


    isCalling = true;


    startBtn.style.display =
        "none";


    endBtn.style.display =
        "inline-flex";


    callTitle.textContent =
        "AI Voice Assistant";


    callStatus.textContent =
        "Connecting to your AI assistant...";


    testGeminiLiveConnection();

});


    // --------------------------------------------------
    // END CALL
    // --------------------------------------------------

    endBtn.addEventListener(
        "click",
        async () => {

            isCalling =
                false;


            // --------------------------------------------------
            // SAVE CONVERSATION TO DATABASE
            // --------------------------------------------------

            if (
                savedCustomerId &&
                businessId &&
                geminiConversationTranscript.trim()
            ) {

                try {

                    const conversationResponse =
                        await fetch(
                            "/ai/api/gemini-live/save-conversation",
                            {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json"
                                },
                                body: JSON.stringify({
                                    business_id: businessId,
                                    customer_id: savedCustomerId,
                                    transcript: geminiConversationTranscript
                                })
                            }
                        );

                    const conversationData =
                        await conversationResponse.json();

                    console.log(
                        "CONVERSATION SAVE RESULT:",
                        conversationData
                    );

                } catch (error) {

                    console.error(
                        "CONVERSATION SAVE ERROR:",
                        error
                    );

                }

            } else {

                console.warn(
                    "CONVERSATION NOT SAVED:",
                    {
                        savedCustomerId,
                        businessId,
                        transcriptAvailable:
                            Boolean(
                                geminiConversationTranscript.trim()
                            )
                    }
                );

            }


            // --------------------------------------------------
            // STOP GEMINI LIVE
            // --------------------------------------------------

            stopGeminiMicrophone();


            if (
                geminiSocket &&
                geminiSocket.readyState ===
                    WebSocket.OPEN
            ) {

                geminiSocket.close(
                    1000,
                    "Call ended by user"
                );

                console.log(
                    "GEMINI LIVE WEBSOCKET CLOSE SENT"
                );

            }


            geminiSocket =
                null;


            geminiSetupComplete =
                false;


            geminiOutputTranscript =
                "";

            geminiConversationTranscript =
                "";

            geminiInputTranscript =
                "";

            savedCustomerId =
                null;


            if (deepgramKeepAliveTimer) {

                clearInterval(
                    deepgramKeepAliveTimer
                );

                deepgramKeepAliveTimer = null;

                console.log(
                    "DEEPGRAM KEEPALIVE TIMER CLEARED"
                );
            }

            if (
                deepgramSocket &&
                deepgramSocket.readyState === WebSocket.OPEN
            ) {

                deepgramSocket.send(
                    JSON.stringify({
                        type: "CloseStream"
                    })
                );

                console.log(
                    "DEEPGRAM CLOSE STREAM SENT"
                );
            }

            if (mediaRecorder) {

                if (
                    mediaRecorder.state === "recording"
                ) {

                    mediaRecorder.stop();

                }

                mediaRecorder =
                    null;

            }

            callOrb.classList.remove(
                "listening"
            );

            removeLiveSpeech();

            // Clear anything waiting to be sent
            aiMessageQueue = [];

            startBtn.style.display =
                "inline-flex";

            endBtn.style.display =
                "none";

            callTitle.textContent =
                "AI Voice Assistant";

            callStatus.textContent =
                "Call ended. Click Start AI Call to begin again.";

        }
    );

});