import axios from "axios";

export const generateText = async (
  prompt,
  systemPrompt = null,
  previousRoomDescription = null,
  playerAction = null
) => {
  try {
    let url = "http://localhost:5001/api/generate";
    let requestData = {
      prompt,
      system_prompt: systemPrompt,
      previous_room_description: previousRoomDescription,
      player_action: playerAction,
    };

    //Initial request
    if (prompt === "Start game") {
      url = "http://localhost:5001/api/game/start";
      requestData = {};
    }

    const response = await axios.post(url, requestData);
    console.log("Response from server:", response.data);
    return response.data.response;
  } catch (error) {
    console.error("Error generating text:", error);
    // return "Error: Could not communicate with the server.";
  }
};
