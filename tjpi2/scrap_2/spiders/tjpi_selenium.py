import scrapy
import unittest
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Tjpi2Spider(scrapy.Spider):
    name = 'tjpi_2'
    allowed_domains = ['www.tjpi.pje.jus.br']

    def start_requests(self):

        self.drive = webdriver.Chrome(executable_path=r'./chromedriver.exe')
        self.drive.get('https://tjpi.pje.jus.br/1g/ConsultaPublica/listView.seam')
        input_num = '0000989-95.2017.8.18.0078'
        input_search1 = self.drive.find_element_by_xpath(
            '//input[@id="fPP:numProcesso-inputNumeroProcessoDecoration:numProcesso-inputNumeroProcesso"]')
        input_search1.send_keys(f'{input_num}')
        sleep(1.5)

        click_search = self.drive.find_element_by_xpath('//input[@id="fPP:searchProcessos"]')
        click_search.click()

        sleep(1.5)

        try:

            open_doc = self.drive.find_element_by_xpath('//a[@href="javascript:void();"]')
            open_doc.click()

            # espera um certo tempo ate confirmar que a outra janela abriu
            WebDriverWait(self.drive, 10).until(lambda d: len(d.window_handles) == 2)

            # troca de janela
            self.drive.switch_to.window(self.drive.window_handles[1])

            # espera a janela carregar para pegar a nova url
            WebDriverWait(self.drive, 10).until(lambda d: d.title != "")

            url = self.drive.current_url

            yield scrapy.Request(url=url,
                                 callback=self.parse)
        except:
            EnvironmentError('Erro')

    def parse(self, response):

        try:
            url = self.drive.current_url
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
            e_Processo = True
            num_processo = response.xpath('//*[@id="j_id140:processoTrfViewView:j_id146"]/div/div[2]/div/'
                                          'text()').get().strip()

            partes = []

            autor_polo = response.xpath('//*[@id="j_id140:j_id272_header"]/text()').get().split()[-1]
            autor_cnpj = response.xpath('//*[@id="j_id140:processoPartesPoloAtivoResumidoList:0:j_id287"]'
                                        '/div/span/text()').get().split(':')[1].split()[0]
            autor_nome = response.xpath('//*[@id="j_id140:processoPartesPoloAtivoResumidoList:0:j_id287"]'
                                        '/div/span/text()').get().split(':')[0].split('-')[0]
            autor_tipo = response.xpath('//*[@id="j_id140:processoPartesPoloAtivoResumidoList:0:j_id287"]'
                                        '/div/span/text()').get().split(':')[1].split()[1][1:-1]
            autor = {
                'cnpj': autor_cnpj,
                'nome': autor_nome,
                'polo': autor_polo,
                'tipo': autor_tipo
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

            def change_page_movt(prev_conteudo):

                page = self.drive.find_element_by_id('j_id140:j_id501:j_id502ArrowInc')
                page.click()

                #slider = self.drive.find_element_by_id('j_id140:j_id501:j_id502Track')
                loader = self.drive.find_element_by_class_name('rich-inslider-track-decor-2')
                WebDriverWait(self.drive, 10).until(EC.invisibility_of_element_located(loader))

                next_conteudo = response.xpath('//*[@id="j_id140:processoEvento:tb"]/tr//text()').getall()

                unittest.TestCase.assertNotEqual(prev_conteudo, next_conteudo, "conteudo nao foi alterado")

            movimentos = []
            indice = 60

            while True:

                i = 0

                container_body = response.xpath('//*[@id="j_id140:processoEvento:tb"]/tr//text()').getall()
                tabela_mov = response.xpath('//*[@id="j_id140:processoEvento:tb"]/tr')

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

                if indice == 0:
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
                change_page_movt(container_body)
                sleep(1)

        finally:
            self.drive.quit()
