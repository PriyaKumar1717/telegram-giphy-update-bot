const TelegramBot = require("node-telegram-bot-api");
require("dotenv").config();
const axios = require("axios");

const token = process.env.TELEGRAM_BOT_TOKEN;
const bot = new TelegramBot(token, { polling: true });

bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;
  bot.sendMessage(
    chatId,
    "Welcome to Giphy Views Tracker Bot! Send /track <project_name> to start tracking views."
  );
});

bot.on("message", (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text.toString().trim();

  // Check if the message is a known command (/start or /track)
  if (text === "/start" || text.startsWith("/track ")) {
    return;
  }

  // Send "Invalid command" message
  bot.sendMessage(
    chatId,
    "Invalid command. Send /start to begin or /track <project_name> to track views and view the first media."
  );
});

bot.onText(/\/track (.+)/, async (msg, match) => {
  const chatId = msg.chat.id;
  const project = match[1]; // Extract project name from user input

  try {
    const { views, mediaUrl } = await fetchViewsFromGiphy(project);
    bot.sendMessage(
      chatId,
      `Total views for ${project} is: ${views} media: ${mediaUrl}`
    );
  } catch (error) {
    bot.sendMessage(chatId, "Error fetching views from Giphy.");
  }
});

async function fetchViewsFromGiphy(project) {
  const apiKey = process.env.GIPHY_API_KEY; //  Giphy API key
  const apiUrl = `https://api.giphy.com/v1/gifs/search?q=${project}&api_key=${apiKey}`;

  try {
    const response = await axios.get(apiUrl);
    const { data } = response.data;
    const firstResult = data[0]; // Get the first result from the API response
    const mediaUrl = firstResult.images.original.url; // Extract the media URL
    const views = response.data.pagination.total_count || 0; // Extract views count
    return { views, mediaUrl };
  } catch (error) {
    throw new Error("Failed to fetch data from Giphy API.");
  }
}

console.log("Bot is running..");
