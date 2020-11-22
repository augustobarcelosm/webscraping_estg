import scrapy
from time import sleep
import json


class Tjpi2Spider(scrapy.Spider):

    name = 'tjpi_1'
    allowed_domains = ['www.tjpi.pje.jus.br']

    def start_requests(self):

        start_url = 'https://tjpi.pje.jus.br/1g/ConsultaPublica/' \
                    'DetalheProcessoConsultaPublica/listView.seam?ca=76b320e49caed7824098ac5e9e5dbcb999009654a1964999'

        yield scrapy.Request(url=start_url,
                            callback=self.parse)

    def parse(self, response):
        partes = []
        url = response.url
        grau_processo = response.xpath('//head/title/text()').get().split('-')[-1].strip()
        orgao = response.xpath('//span[@id="j_id140:processoTrfViewView:j_id217"]/div[1]/div/text()[1]').getall()[-1].strip()
        origem = response.xpath('//span[@id="j_id140:processoTrfViewView:j_id193"][1]/'
                                'div/div/text()').getall()[-1].strip()
        nome_processural = response.xpath('//span[@id="j_id140:processoTrfViewView:j_id169"][1]'
                                              '/div/div/text()').getall()[-1].strip().split('(')[0]
        codigo = response.xpath('//span[@id="j_id140:processoTrfViewView:j_id169"][1]'
                                    '/div/div/text()').getall()[-1].strip().split('(')[1]
        codigoCNJ = codigo.replace(')', '')

        data = response.xpath('//*[@id="j_id140:processoTrfViewView:j_id158"]/div/div[2]/text()').get().strip()
        e_Processo = ''
        num_processo = response.xpath(
                '//*[@id="j_id140:processoTrfViewView:j_id146"]/div/div[2]/div/text()').get().strip()

        polo = response.xpath('//*[@id="j_id140:j_id272_header"]/text()').get().split()[-1]
        cnpj = response.xpath('//*[@id="j_id140:processoPartesPoloAtivoResumidoList:0:j_id287"]'
                                  '/div/span/text()').get().split(':')[1].split()[0]
        nome = response.xpath('//*[@id="j_id140:processoPartesPoloAtivoResumidoList:0:j_id287"]'
                                  '/div/span/text()').get().split(':')[0].split('-')[0]
        tipo = response.xpath('//*[@id="j_id140:processoPartesPoloAtivoResumidoList:0:j_id287"]'
                                  '/div/span/text()').get().split(':')[1].split()[1][1:-1]
        autor = {
            'cnpj': cnpj,
            'nome': nome,
            'polo': polo,
            'tipo': tipo
                }

        partes.append(autor)

        polo_passivo = response.xpath('//*[@id="j_id140:processoPartesPoloPassivoResumidoList:tb"]/tr')
        lista_adv = response.xpath('.//td[@class="rich-table-cell "]/span/div/span[@class=""]/text()').getall()
        adv = [{
                'cpf': adv.split()[-2],
                'OAB': {
                        'uf': adv.split('-')[1].split()[-1][:2],
                        'numero': adv.split('-')[1].split()[-1][2:]
                        },
                'nome': adv.split('-')[0],
                'tipo': adv.split()[-1][1:-1]
                } for adv in lista_adv]
        for part in polo_passivo:
            tipo_cpf_cnpj = part.xpath('.//td/span/div/span/text()').get().split(':')[0].split('-')[-1]
            cpf_cnpj = part.xpath('.//td/span/div/span/text()').get().split(':')[1].split('(')[0]
            nome = part.xpath('.//td/span/div/span/text()').get().split(':')[0].split('-')[0]
            polo = response.xpath('.//*[@id="j_id140:j_id324_header"]//text()').get().split()[1].upper()
            tipo = part.xpath('.//td/span/div/span/text()').get().split(':')[1].split('(')[1].replace(')', '')
            if tipo == 'REU':
                partes.append({
                    tipo_cpf_cnpj: cpf_cnpj,
                    'nome': nome,
                    'polo': polo,
                    'tipo': tipo,
                    'advogados': [
                        adv.pop(0),
                        adv.pop(0),
                                   ]
                                })

        indice = 60
        tabela_mov = response.xpath('//*[@id="j_id140:processoEvento:tb"]/tr')
        movimentos = []

        while True:

            i = 0

            for mov in tabela_mov:

                data = mov.xpath(f'.//*[@id="j_id140:processoEvento:{i}:j_id465"]/text()').get().split('-')[0]
                e_movimento = True
                nome = mov.xpath(f'.//*[@id="j_id140:processoEvento:{i}:j_id465"]/text()').get().split('-')[1]
                movimentos.append({
                    'data': data,
                    'indice': indice,
                    'eMovimento': e_movimento,
                    'nomeOriginal': [nome]
                })
                indice -= 1
                i += 1

            yield {
                       'uf': 'PI',
                       'partes': partes,
                       'movimentos': movimentos,
                       'urlProcesso': url,
                       'grauProcesso': grau_processo,
                       'orgaoJulgador': orgao,
                       'unidadeOrigem': origem,
                       'classeProcessual': {
                           'nome': nome_processural,
                           'codigoCNJ': codigoCNJ
                         },
                       'dataDistribuicao': data,
                       'eProcesso': e_Processo,
                       'numeroProcessoUnico': num_processo
                   }
            break










