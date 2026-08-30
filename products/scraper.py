# products/scraper.py
import requests
from bs4 import BeautifulSoup
from decimal import Decimal
import json


class ProductScraper:
    """Scraper para extrair dados de produtos"""
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    
    def __init__(self, url, platform):
        self.url = url
        self.platform = platform
        self.data = {}
    
    def scrape(self):
        if self.platform == 'mercado_livre':
            return self.scrape_mercado_livre()
        elif self.platform == 'amazon':
            return self.scrape_amazon()
        elif self.platform == 'shopee':
            return self.scrape_shopee()
        return self.data
    
    def scrape_mercado_livre(self):
        """Extrai dados do Mercado Livre"""
        try:
            response = requests.get(self.url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Tenta extrair dados do JSON embutido
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    json_data = json.loads(script.string)
                    if isinstance(json_data, list):
                        json_data = json_data[0]
                    
                    if json_data.get('@type') == 'Product':
                        self.data['name'] = json_data.get('name', '')
                        
                        if json_data.get('image'):
                            self.data['main_image'] = json_data['image']
                        
                        if json_data.get('offers'):
                            offers = json_data['offers']
                            if isinstance(offers, list):
                                offers = offers[0]
                            self.data['current_price'] = Decimal(str(offers.get('price', '0')))
                        
                        if json_data.get('description'):
                            self.data['short_description'] = json_data['description'][:300]
                        
                        return self.data
                except (json.JSONDecodeError, AttributeError):
                    continue
            
            # Fallback: busca direta
            title = soup.find('h1')
            if title and not self.data.get('name'):
                self.data['name'] = title.text.strip()[:200]
            
            # Busca preço
            price_meta = soup.find('meta', {'itemprop': 'price'})
            if price_meta and price_meta.get('content'):
                self.data['current_price'] = Decimal(price_meta['content'])
            
            # Busca imagem
            img_meta = soup.find('meta', {'itemprop': 'image'})
            if img_meta and img_meta.get('content'):
                self.data['main_image'] = img_meta['content']
            
            return self.data
            
        except Exception as e:
            self.data['error'] = str(e)
            return self.data
    
    def scrape_amazon(self):
        """Extrai dados da Amazon"""
        try:
            response = requests.get(self.url, headers=self.HEADERS, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = soup.find('span', id='productTitle')
            if title:
                self.data['name'] = title.text.strip()[:200]
            
            price = soup.find('span', class_='a-price-whole')
            if price:
                price_text = price.text.replace('.', '').replace(',', '.')
                self.data['current_price'] = Decimal(price_text)
            
            image = soup.find('img', id='landingImage')
            if image and image.get('src'):
                self.data['main_image'] = image['src']
            
            return self.data
            
        except Exception as e:
            self.data['error'] = str(e)
            return self.data
    
    def scrape_shopee(self):
        """Extrai dados da Shopee"""
        try:
            response = requests.get(self.url, headers=self.HEADERS, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = soup.find('div', class_='attM6y')
            if title:
                self.data['name'] = title.text.strip()[:200]
            
            price = soup.find('div', class_='_2Shl1j')
            if price:
                price_text = price.text.replace('R$', '').replace('.', '').replace(',', '.').strip()
                self.data['current_price'] = Decimal(price_text)
            
            image = soup.find('img', class_='_3RUs_Z')
            if image and image.get('src'):
                self.data['main_image'] = image['src']
            
            return self.data
            
        except Exception as e:
            self.data['error'] = str(e)
            return self.data