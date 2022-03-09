import json
import aiohttp
from understat import Understat
import asyncio

async def main():
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        fixtures = await understat.get_league_results(
            "epl",
            2021
        )
        with open('fixtures.json', 'w') as outf:
            json.dump(fixtures, outf)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())


# async def main():
#     async with aiohttp.ClientSession() as session:
#         understat = Understat(session)
#         players = await understat.get_match_players()
#         print(json.dumps(players))

# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())