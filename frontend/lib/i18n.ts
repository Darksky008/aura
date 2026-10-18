import type { Lang } from "@/types";

/** UI strings for every supported language. Adding a language = add one block here + a TTS voice on the backend. */
export interface Strings {
  begin: string; beginHint: string; tapToBegin: string; greeting: (restaurant: string) => string; restaurantName: (apiName: string) => string;
  idleHint: string; listening: string; thinking: string; speaking: string; errorState: string;
  askPlaceholder: string; send: string; voiceMode: string; chatMode: string; menu: string; mic: string; stopListening: string; sendNow: string;
  tapToInterrupt: string; quickTitle: string; prompts: string[]; language: string; retry: string; clear: string; heard: string;
  didntCatch: string; stillNoCatch: string; micBlocked: string; micUnsupported: string; sttDown: string; serviceDown: string; voiceFallback: string; voiceNone: string;
  handsFree: string; voiceReplies: string; sessionExpired: string; switched: string; offlineNote: string; typeInstead: string;
  tools: Record<string, string>;
  menuTitle: string; menuSub: string; filters: Record<string, string>; spice: Record<string, string>; calories: string; allergens: string; ingredients: string; dietary: string;
  vegetarian: string; vegan: string; glutenFree: string; chefSpecial: string; available: string; unavailable: string; priceOnRequest: string; close: string;
  askAbout: string; askWhy: string; none: string; unknown: string; nonVeg: string; backToConcierge: string; yes: string; no: string; nothingHere: string; confirmWithTeam: string;
}

const en: Strings = {
  begin: "Meet AURA", beginHint: "Your digital dining concierge. Speak or type in English, தமிழ் or हिन्दी.", tapToBegin: "Tap to begin",
  greeting: (_r) => "Welcome to Aura! What can I help you discover from our menu today?",
  restaurantName: (n) => n,
  idleHint: "Tap the microphone and ask me anything", listening: "Listening…", thinking: "One moment…", speaking: "Speaking", errorState: "Something went wrong",
  askPlaceholder: "Ask anything about our menu", send: "Send", voiceMode: "Voice", chatMode: "Chat", menu: "Menu", mic: "Speak", stopListening: "Tap when you're done", sendNow: "Send now",
  tapToInterrupt: "Tap to interrupt", quickTitle: "Popular questions", language: "Language", retry: "Retry", clear: "Clear conversation", heard: "I heard",
  didntCatch: "Sorry, I didn't quite catch that. Could you say it once more?", stillNoCatch: "I'm still having trouble hearing you. You can also type your question.",
  micBlocked: "Microphone access is blocked. Please allow the microphone in your browser, or switch to Chat.", micUnsupported: "Voice input isn't supported on this device. Please use Chat.",
  sttDown: "Voice recognition is unavailable right now. Please use Chat.", serviceDown: "We can't reach the concierge service. Please try again.",
  voiceFallback: "Using this device's voice.", voiceNone: "Spoken replies aren't available on this device for this language. Replies appear as text.",
  handsFree: "Hands-free", voiceReplies: "Spoken replies", sessionExpired: "That conversation expired. Starting fresh.", switched: "Of course, we can continue in English.",
  offlineNote: "Offline demo mode - add a Groq key for full AI", typeInstead: "Type instead",
  tools: { search_menu: "Searching the menu…", get_dish_details: "Looking up the dish…", get_ingredients: "Looking up ingredients…", get_allergens: "Checking allergen information…",
    get_dishes_by_dietary_preference: "Checking dietary options…", get_dishes_by_spice_level: "Checking spice levels…", get_today_specials: "Checking today's specials…",
    get_available_dishes: "Checking availability…", recommend_dishes: "Finding the right dishes…", compare_dishes: "Comparing the dishes…", search_knowledge: "Checking our restaurant notes…" },
  menuTitle: "The Menu", menuSub: "Contemporary Indian cuisine",
  filters: { all: "All", starters: "Starters", "main-course": "Main Course", "south-indian": "South Indian", desserts: "Desserts", chef: "Chef Specials", vegetarian: "Vegetarian", vegan: "Vegan" },
  spice: { none: "No spice", mild: "Mild", medium: "Medium", high: "Hot" }, calories: "Calories", allergens: "Allergens", ingredients: "Ingredients", dietary: "Dietary",
  vegetarian: "Vegetarian", vegan: "Vegan", glutenFree: "Gluten free", chefSpecial: "Chef Special", available: "Available", unavailable: "Currently unavailable", priceOnRequest: "Price on request", close: "Close",
  askAbout: "Ask AURA about this dish", askWhy: "Why should I try this dish?", none: "None listed", unknown: "Not specified", nonVeg: "Non-vegetarian", backToConcierge: "Back to AURA", yes: "Yes", no: "No", nothingHere: "Nothing here yet.",
  confirmWithTeam: "Please confirm allergies with our restaurant team.",
  prompts: ["What are today's specials?", "Recommend a vegetarian dish.", "Which dishes are mild?", "What are the ingredients in Chicken Biryani?", "Does anything contain nuts?",
    "What is the lightest main course?", "Compare Paneer Tikka and Masala Dosa.", "I want something vegan.", "What dessert do you recommend?"],
};

const ta: Strings = {
  begin: "AURA-வை சந்தியுங்கள்", beginHint: "உங்கள் டிஜிட்டல் உணவு உதவியாளர். தமிழ், English அல்லது हिन्दी-யில் பேசலாம் அல்லது தட்டச்சு செய்யலாம்.", tapToBegin: "தொடங்க தட்டவும்",
  greeting: (_r) => "Aura-வுக்கு வரவேற்கிறோம்! இன்று எங்கள் மெனுவில் நீங்கள் எதைக் கண்டறிய நான் உதவ வேண்டும்?",
  restaurantName: (n) => (n === "Saffron Terrace" ? "சாஃப்ரன் டெரஸ்" : n),
  idleHint: "மைக்கைத் தட்டி எதுவும் கேளுங்கள்", listening: "கேட்கிறேன்…", thinking: "ஒரு நிமிடம்…", speaking: "பேசுகிறேன்", errorState: "ஏதோ தவறு நேர்ந்தது",
  askPlaceholder: "எங்கள் மெனு பற்றி எதுவும் கேளுங்கள்", send: "அனுப்பு", voiceMode: "குரல்", chatMode: "உரையாடல்", menu: "மெனு", mic: "பேசுங்கள்", stopListening: "முடிந்ததும் தட்டவும்", sendNow: "இப்போது அனுப்பு",
  tapToInterrupt: "இடைமறிக்கத் தட்டவும்", quickTitle: "பிரபலமான கேள்விகள்", language: "மொழி", retry: "மீண்டும் முயற்சி", clear: "உரையாடலை அழி", heard: "நான் கேட்டது",
  didntCatch: "மன்னிக்கவும், எனக்குச் சரியாகக் கேட்கவில்லை. மீண்டும் ஒருமுறை சொல்ல முடியுமா?", stillNoCatch: "இன்னும் எனக்குக் கேட்பதில் சிரமம் உள்ளது. உங்கள் கேள்வியைத் தட்டச்சும் செய்யலாம்.",
  micBlocked: "மைக்ரோஃபோன் அனுமதி தடுக்கப்பட்டுள்ளது. உலாவியில் அனுமதி அளிக்கவும் அல்லது உரையாடல் முறைக்கு மாறவும்.", micUnsupported: "இந்தச் சாதனத்தில் குரல் உள்ளீடு ஆதரிக்கப்படவில்லை. உரையாடல் முறையைப் பயன்படுத்தவும்.",
  sttDown: "குரல் அறிதல் இப்போது கிடைக்கவில்லை. உரையாடல் முறையைப் பயன்படுத்தவும்.", serviceDown: "சேவையுடன் இணைக்க முடியவில்லை. மீண்டும் முயற்சிக்கவும்.",
  voiceFallback: "இந்தச் சாதனத்தின் குரலைப் பயன்படுத்துகிறோம்.", voiceNone: "இந்த மொழிக்கு இந்தச் சாதனத்தில் குரல் பதில் இல்லை. பதில்கள் எழுத்தில் காட்டப்படும்.",
  handsFree: "கைகள் இல்லாமல்", voiceReplies: "குரல் பதில்கள்", sessionExpired: "அந்த உரையாடல் காலாவதியானது. புதிதாகத் தொடங்குகிறோம்.", switched: "சரி, தமிழில் தொடரலாம்.",
  offlineNote: "ஆஃப்லைன் டெமோ - முழு AI-க்கு Groq key சேர்க்கவும்", typeInstead: "தட்டச்சு செய்",
  tools: { search_menu: "மெனுவில் தேடுகிறேன்…", get_dish_details: "உணவின் விவரங்களைப் பார்க்கிறேன்…", get_ingredients: "பொருட்களைப் பார்க்கிறேன்…", get_allergens: "ஒவ்வாமை தகவலைச் சரிபார்க்கிறேன்…",
    get_dishes_by_dietary_preference: "உணவு விருப்பங்களைச் சரிபார்க்கிறேன்…", get_dishes_by_spice_level: "காரத்தின் அளவைச் சரிபார்க்கிறேன்…", get_today_specials: "இன்றைய சிறப்புகளைப் பார்க்கிறேன்…",
    get_available_dishes: "கிடைக்கும் உணவுகளைப் பார்க்கிறேன்…", recommend_dishes: "பொருத்தமான உணவுகளைத் தேடுகிறேன்…", compare_dishes: "உணவுகளை ஒப்பிடுகிறேன்…", search_knowledge: "உணவகக் குறிப்புகளைப் பார்க்கிறேன்…" },
  menuTitle: "மெனு", menuSub: "நவீன இந்திய உணவு",
  filters: { all: "அனைத்தும்", starters: "ஸ்டார்டர்கள்", "main-course": "முதன்மை உணவு", "south-indian": "தென்னிந்திய", desserts: "இனிப்புகள்", chef: "செஃப் சிறப்பு", vegetarian: "சைவம்", vegan: "வீகன்" },
  spice: { none: "காரம் இல்லை", mild: "மிதமான", medium: "நடுத்தரம்", high: "அதிக காரம்" }, calories: "கலோரி", allergens: "ஒவ்வாமைகள்", ingredients: "பொருட்கள்", dietary: "உணவு வகை",
  vegetarian: "சைவம்", vegan: "வீகன்", glutenFree: "குளூட்டன் இல்லாதது", chefSpecial: "செஃப் சிறப்பு", available: "கிடைக்கும்", unavailable: "தற்போது கிடைக்காது", priceOnRequest: "விலை கேட்டால் தெரிவிக்கப்படும்", close: "மூடு",
  askAbout: "இந்த உணவு பற்றி AURA-விடம் கேளுங்கள்", askWhy: "இந்த உணவை நான் ஏன் முயற்சிக்க வேண்டும்?", none: "எதுவும் குறிப்பிடப்படவில்லை", unknown: "குறிப்பிடப்படவில்லை", nonVeg: "அசைவம்", backToConcierge: "AURA-வுக்குத் திரும்பு", yes: "ஆம்", no: "இல்லை", nothingHere: "இன்னும் எதுவும் இல்லை.",
  confirmWithTeam: "ஒவ்வாமை குறித்து எங்கள் உணவகக் குழுவிடம் உறுதிசெய்து கொள்ளுங்கள்.",
  prompts: ["இன்றைய சிறப்பு உணவுகள் என்ன?", "ஒரு சைவ உணவைப் பரிந்துரைக்கவும்.", "எந்த உணவுகள் காரம் குறைவாக உள்ளன?", "சிக்கன் பிரியாணியில் என்னென்ன பொருட்கள் உள்ளன?", "ஏதாவது உணவில் கொட்டைகள் உள்ளனவா?",
    "மிகவும் லேசான முதன்மை உணவு எது?", "பனீர் டிக்கா மற்றும் மசாலா தோசையை ஒப்பிடுங்கள்.", "எனக்கு வீகன் உணவு வேண்டும்.", "இனிப்புக்கு எதைப் பரிந்துரைக்கிறீர்கள்?"],
};

const hi: Strings = {
  begin: "AURA से मिलिए", beginHint: "आपकी डिजिटल डाइनिंग कंसीयर्ज। हिन्दी, English या தமிழ் में बोलें या लिखें।", tapToBegin: "शुरू करने के लिए टैप करें",
  greeting: (_r) => "Aura में आपका स्वागत है! आज हमारे मेनू से क्या जानने में मैं आपकी मदद कर सकती हूँ?",
  restaurantName: (n) => (n === "Saffron Terrace" ? "सैफ्रन टेरेस" : n),
  idleHint: "माइक्रोफ़ोन दबाएँ और कुछ भी पूछें", listening: "सुन रही हूँ…", thinking: "एक क्षण…", speaking: "बोल रही हूँ", errorState: "कुछ गड़बड़ हो गई",
  askPlaceholder: "हमारे मेनू के बारे में कुछ भी पूछें", send: "भेजें", voiceMode: "आवाज़", chatMode: "चैट", menu: "मेनू", mic: "बोलें", stopListening: "बोलना खत्म होने पर टैप करें", sendNow: "अभी भेजें",
  tapToInterrupt: "रोकने के लिए टैप करें", quickTitle: "लोकप्रिय सवाल", language: "भाषा", retry: "फिर कोशिश करें", clear: "बातचीत साफ़ करें", heard: "मैंने सुना",
  didntCatch: "क्षमा करें, मैं ठीक से सुन नहीं पाई। क्या आप एक बार फिर कह सकते हैं?", stillNoCatch: "मुझे अब भी सुनने में दिक्कत हो रही है। आप अपना सवाल लिखकर भी पूछ सकते हैं।",
  micBlocked: "माइक्रोफ़ोन की अनुमति रुकी हुई है। कृपया ब्राउज़र में अनुमति दें या चैट पर जाएँ।", micUnsupported: "इस डिवाइस पर आवाज़ से इनपुट समर्थित नहीं है। कृपया चैट का उपयोग करें।",
  sttDown: "आवाज़ पहचान अभी उपलब्ध नहीं है। कृपया चैट का उपयोग करें।", serviceDown: "सेवा से संपर्क नहीं हो पा रहा। कृपया फिर कोशिश करें।",
  voiceFallback: "इस डिवाइस की आवाज़ का उपयोग हो रहा है।", voiceNone: "इस भाषा के लिए इस डिवाइस पर बोलकर जवाब उपलब्ध नहीं है। जवाब लिखित रूप में दिखेंगे।",
  handsFree: "हैंड्स-फ्री", voiceReplies: "बोलकर जवाब", sessionExpired: "वह बातचीत समाप्त हो गई थी। नए सिरे से शुरू कर रहे हैं।", switched: "ज़रूर, हम हिन्दी में बात जारी रखते हैं।",
  offlineNote: "ऑफ़लाइन डेमो - पूर्ण AI के लिए Groq key जोड़ें", typeInstead: "लिखकर पूछें",
  tools: { search_menu: "मेनू में खोज रही हूँ…", get_dish_details: "व्यंजन की जानकारी देख रही हूँ…", get_ingredients: "सामग्री देख रही हूँ…", get_allergens: "एलर्जी की जानकारी जाँच रही हूँ…",
    get_dishes_by_dietary_preference: "आहार विकल्प जाँच रही हूँ…", get_dishes_by_spice_level: "तीखेपन का स्तर जाँच रही हूँ…", get_today_specials: "आज के स्पेशल देख रही हूँ…",
    get_available_dishes: "उपलब्धता देख रही हूँ…", recommend_dishes: "सही व्यंजन ढूँढ रही हूँ…", compare_dishes: "व्यंजनों की तुलना कर रही हूँ…", search_knowledge: "रेस्तरां के नोट्स देख रही हूँ…" },
  menuTitle: "मेनू", menuSub: "समकालीन भारतीय व्यंजन",
  filters: { all: "सभी", starters: "स्टार्टर्स", "main-course": "मुख्य व्यंजन", "south-indian": "दक्षिण भारतीय", desserts: "मिठाई", chef: "शेफ स्पेशल", vegetarian: "शाकाहारी", vegan: "वीगन" },
  spice: { none: "बिना मसाले", mild: "हल्का", medium: "मध्यम", high: "तीखा" }, calories: "कैलोरी", allergens: "एलर्जी", ingredients: "सामग्री", dietary: "आहार",
  vegetarian: "शाकाहारी", vegan: "वीगन", glutenFree: "ग्लूटेन-मुक्त", chefSpecial: "शेफ स्पेशल", available: "उपलब्ध", unavailable: "फ़िलहाल उपलब्ध नहीं", priceOnRequest: "कीमत पूछने पर बताई जाएगी", close: "बंद करें",
  askAbout: "इस व्यंजन के बारे में AURA से पूछें", askWhy: "मुझे यह व्यंजन क्यों आज़माना चाहिए?", none: "कोई सूचीबद्ध नहीं", unknown: "निर्दिष्ट नहीं", nonVeg: "मांसाहारी", backToConcierge: "AURA पर वापस", yes: "हाँ", no: "नहीं", nothingHere: "अभी यहाँ कुछ नहीं है।",
  confirmWithTeam: "कृपया एलर्जी के बारे में हमारी रेस्तरां टीम से पुष्टि करें।",
  prompts: ["आज के स्पेशल क्या हैं?", "कोई शाकाहारी व्यंजन सुझाइए।", "कौन से व्यंजन कम तीखे हैं?", "चिकन बिरयानी में क्या-क्या सामग्री है?", "क्या किसी व्यंजन में मेवे (नट्स) हैं?",
    "सबसे हल्का मेन कोर्स कौन सा है?", "पनीर टिक्का और मसाला डोसा की तुलना करें।", "मुझे कोई वीगन व्यंजन चाहिए।", "मिठाई में आप क्या सुझाएँगे?"],
};

export const STRINGS: Record<Lang, Strings> = { en, ta, hi };
export const LANG_LABEL: Record<Lang, string> = { en: "English", ta: "தமிழ்", hi: "हिन्दी" };
export const LANG_LOCALE: Record<Lang, string> = { en: "en-IN", ta: "ta-IN", hi: "hi-IN" };

/** Pick a dish/category name in the guest's language, falling back to English. */
export const localName = (names: Record<string, string> | undefined, fallback: string, lang: Lang) => (lang !== "en" && names?.[lang]) || fallback;

/** Detect the script of a reply so the right voice/language label is used. */
export function detectLang(text: string, fallback: Lang): Lang {
  const ta = (text.match(/[\u0B80-\u0BFF]/g) ?? []).length;
  const hi = (text.match(/[\u0900-\u097F]/g) ?? []).length;
  if (!ta && !hi) return fallback === "en" || /[A-Za-z]{4,}/.test(text) ? "en" : fallback;
  return ta >= hi ? "ta" : "hi";
}
