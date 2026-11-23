import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class Scene(BaseModel):
    scene_id: int
    title: str = "Scene"
    duration: float = 3.5  # Duration in seconds
    voice_script: str  # Narration spoken in this scene
    visual_prompt: str  # Prompt for AI image generation or stock query
    motion_type: str = "zoom_in"  # zoom_in, pan_right, zoom_out, static
    transition: str = "fade"  # fade, wipe, cut

class VideoProductionPlan(BaseModel):
    title: str
    aspect_ratio: str = "9:16"  # 9:16 for Reels/Shorts or 16:9 for Widescreen
    music_genre: str = "tech_ambient"  # tech_ambient, lofi, cinematic, upbeat
    voice_name: str = "en-US-ChristopherNeural"
    scenes: List[Scene]

def generate_default_storyboard(
    topic: str,
    aspect_ratio: str = "9:16",
    voice: str = "en-US-ChristopherNeural",
    music_genre: str = "tech_ambient"
) -> VideoProductionPlan:
    """Generates a high-converting 3-scene cinematic storyboard if LLM does not specify all details."""
    clean_topic = topic.strip()
    return VideoProductionPlan(
        title=clean_topic[:40],
        aspect_ratio=aspect_ratio,
        music_genre=music_genre,
        voice_name=voice,
        scenes=[
            Scene(
                scene_id=1,
                title="The Hook",
                duration=3.5,
                voice_script=f"What if everything you knew about {clean_topic} was about to change?",
                visual_prompt=f"cinematic dramatic opening shot, high concept futuristic visualization of {clean_topic}, 8k, volumetric lighting, photorealistic, Unreal Engine 5 render",
                motion_type="zoom_in",
                transition="fade"
            ),
            Scene(
                scene_id=2,
                title="The Breakthrough",
                duration=4.5,
                voice_script=f"Traditional methods are slow and broken. But modern autonomous technology flips the game completely.",
                visual_prompt=f"high tech glowing holographic interface, advanced AI systems computing data for {clean_topic}, cinematic depth of field, neon accents, dark mode aesthetic",
                motion_type="pan_right",
                transition="fade"
            ),
            Scene(
                scene_id=3,
                title="The Payoff",
                duration=4.0,
                voice_script=f"This is the new standard. Welcome to the future.",
                visual_prompt=f"epic breathtaking hero shot, triumphant cinematic climax, sleek modern product and human connection, glowing horizon, cinematic 8k masterpiece",
                motion_type="zoom_out",
                transition="cut"
            )
        ]
    )
