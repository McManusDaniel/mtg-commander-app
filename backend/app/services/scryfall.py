import httpx, asyncio
from tqdm import tqdm

## Easier to see error title ##
class CardFetchError(Exception):
    pass

## Create a Scryfall Client class so connection is only created once ##
class ScryfallService:
    def __init__(self, rate_limit_ms = 100):
        self.base_card_url = "https://api.scryfall.com/cards/named"
        self.rate_limit_ms = rate_limit_ms
        self.rate_limit_lock = asyncio.Semaphore(1)
        self.client = httpx.AsyncClient(timeout=10)
        self._card_cache: dict[str, dict] = {}
        self._rulings_cache: dict[str, list] = {}
        
    async def close(self):
        await self.client.aclose()
        
    ## Core card-fetching function, single card ##
    async def fetch_card_data(self, card:str) -> dict:
        """
        Fetch select metadata from Scryfall for a single card. Uses EXACT name match in Scryfall API, implements 100ms delay.

        Args:
            card (str): EXACT card name, including capitalization.

        Raises:
            CardFetchError: Raises if Scryfall doesn't have a matching card in their database.

        Returns:
            dict: Metadata of the card including name, image_urls, oracle_text, etc.
        """
        
        if card in self._card_cache:
            return self._card_cache[card]
        else:
            async with self.rate_limit_lock:
                await asyncio.sleep(self.rate_limit_ms / 1000)
                response = await self.client.get(self.base_card_url, params={"fuzzy":card})
                if response.status_code != 200:
                    raise CardFetchError(f"Card '{card}' not found in Scryfall database.")
                data = response.json()
                
                card_metadata = {
                    "name": data.get("name"),
                    "id": data.get("id"),
                    "image_url": {
                        "normal": data.get("image_uris", {}).get("normal"),
                        "border_crop": data.get("image_uris", {}).get("border_crop"),
                        "small": data.get("image_uris", {}).get("small")
                    },
                    "mana_cost": data.get("mana_cost"),
                    "cmc": data.get("cmc"),
                    "type": data.get("type_line"),
                    "colors": data.get("colors"),
                    "oracle_text": data.get("oracle_text"),
                    "keywords": data.get("keywords"),
                    "legality": data.get("legalities", {}).get("commander")
                }
                
            self._card_cache[card] = card_metadata
                    
            return card_metadata

    ## Get card rulings for card ##
    async def fetch_rulings(self, card_id:str) -> list:
        """
        Get rulings data for a given card ID.

        Args:
            id (str): Scryfall unique card ID.

        Raises:
            CardFetchError: Raises if Scryfall doesn't have a matching card in their database.

        Returns:
            list: A list of card-specific rulings and their dates.
        """
        if card_id in self._rulings_cache:
            return self._rulings_cache[card_id]
    
        else:
            async with self.rate_limit_lock:
                await asyncio.sleep(self.rate_limit_ms / 1000)
                response = await self.client.get(f"https://api.scryfall.com/cards/{card_id}/rulings")
                if response.status_code != 200:
                    raise CardFetchError(f"Card ID '{card_id}' not found in Scryfall database.")
                data = response.json().get("data", [])
                
                clean_rulings = []
                
                for ruling in data:
                    rule = f"[{ruling.get('published_at')}] {ruling.get('comment')}"
                    clean_rulings.append(rule)
                
            self._rulings_cache[card_id] = clean_rulings
                
            return clean_rulings
    
    ## Combined Single Card Pull ##
    async def fetch_full_card(self, card:str) -> dict:
        card_data = await self.fetch_card_data(card)
        card_rulings = await self.fetch_rulings(card_data["id"])
        card_data["rulings"] = card_rulings
        
        return card_data
    
    ## Batch the core card-fetching function ##
    async def batch_fetch_card_data(self, cards:list[str], progress:bool = False) -> list:
        """
        Fetch select metadata from Scryfall for a list of cards. Uses EXACT name match in Scryfall API, implements 100ms delay.

        Args:
            cards (list[str]): List of EXACT card names, including capitalization.
            progress (bool, optional): True to show a progress bar in console. Defaults to False.

        Returns:
            list: List of card metadata dictionaries.
        """
        tasks = [asyncio.create_task(self.fetch_full_card(card)) for card in cards]
        
        data = []
        if progress: 
            with tqdm(total=len(tasks)) as pbar:
                for task in asyncio.as_completed(tasks):
                    result = await task
                    data.append(result)
                    pbar.update(1)
        else: 
            data = await asyncio.gather(*tasks)
            
        return data