import discord
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import OpenAI
load_dotenv()

class LinkResponse(BaseModel):
    title: str
    summary: str
    date: str

llm_client = OpenAI(api_key=os.environ.get("OPENAI_TOKEN"))
def process_link(link):    
    completion = llm_client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "The following is a link to an article- extract the title and date (MM/YYYY), and provide a paragraph-length summary of the content. Be as neutral as possible while still presenting the facts."},
            {"role": "user", "content": f"{link}"},
        ],
        response_format=LinkResponse,
    )
    return completion.choices[0].message.parsed

# For simplicity here, we store the token in code. In production, consider using environment variables.
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

NEW_LINKS_FILE = "new_links.txt"
TARGETS_FILE = "targets.txt"

intents = discord.Intents.default()
client = discord.Client(intents=intents)

def build_embed(link):
    additional_info: LinkResponse = process_link(link)
    embed = discord.Embed()
    embed.title = additional_info.title
    embed.url = link
    embed.description = f"_{additional_info.date}_— {additional_info.summary}"
    embed.set_footer(text=link)
    return embed

@client.event
async def on_ready():
    print(f"Bot logged in as {client.user}")

    # 1. Load new links
    if not os.path.exists(NEW_LINKS_FILE):
        print(f"'{NEW_LINKS_FILE}' not found. No links to post.")
        await client.close()
        return

    with open(NEW_LINKS_FILE, "r", encoding="utf-8") as f:
        new_links = [line.strip() for line in f if line.strip()]

    if not new_links:
        print("No new links found to dispatch.")
        await client.close()
        return

    # 2. Read target channel IDs
    if not os.path.exists(TARGETS_FILE):
        print(f"'{TARGETS_FILE}' not found. No channels to post to.")
        await client.close()
        return

    with open(TARGETS_FILE, "r", encoding="utf-8") as f:
        channel_ids = [line.strip() for line in f if line.strip()]

    # 3. Post the new links to each channel
    print("Building Embeds")
    embeds = [build_embed(link) for link in new_links]
    for channel_id_str in channel_ids:
        try:
            channel_id = int(channel_id_str)
        except ValueError:
            print(f"Skipping invalid channel ID: {channel_id_str}")
            continue

        channel = client.get_channel(channel_id)
        if channel is None:
            print(f"Could not find channel with ID {channel_id}. Skipping.")
            continue

        print(f"Posting {len(new_links)} new links to channel {channel_id}...")
        for embed in embeds:
            await channel.send(embed=embed)

    # (Optional) Clear `new_links.txt` after posting
    # open(NEW_LINKS_FILE, "w").close()

    # 4. Shutdown the bot
    print("All links posted. Shutting down.")
    await client.close()

if __name__ == "__main__":
    client.run(DISCORD_BOT_TOKEN)
