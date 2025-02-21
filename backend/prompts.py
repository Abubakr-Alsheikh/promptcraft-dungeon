def generate_room_prompt(theme, difficulty):
    prompt = f"""
    You are a dungeon master describing a scene in a text-based adventure game.
    Describe a dungeon room based on the following:

    Theme: {theme}
    Difficulty: {difficulty}

    The description should be concise (around 2-3 sentences) and engaging.
    Include details about the room's appearance, any immediate exits, and a hint of potential danger or intrigue. Do not include any character actions.
    """
    return prompt.strip()  # remove extra spaces


def generate_follow_up_prompt(previous_room_description, player_action):
    prompt = f"""
  {previous_room_description}

  The player decides to: '{player_action}'.

  Describe concisely (2-3 sentences) what happens next. Maintain the established tone.
  """
    return prompt.strip()
