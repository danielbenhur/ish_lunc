# ISH_LUNC - README

Este repositório contém scripts com finalidade principal de calcular o **Índice de Segurança Hídrica LabGest-UFES/Neades-CPID (ISH_LUNC)** por ottobacias e agregar/visualizar esses resultados em unidades de apresentação (municípios, estados, regiões etc.). O projeto engloba como padrão as funções na dimensão humana, presentes na pasta functions_module_ish_hum; depois dos cálculos puxados pelo motorCalculo.py, usa-se o joinISH.py para gerar um gpkg para formar os mapas verificáveis em GIS.

![Fluxograma do ISH-LUNC](./ISH-LUNC_fluxograma.svg)

## **Veja o modelo aplicado:** [AdaptaES](https://adaptaes.incaper.es.gov.br/ish)

## **Arquitetura**
```
ISH_LUNC/
├─ joinISH.py                   # script que junta csv's calculados em um arquivo .gpkg para funcionalidade de mapa em GIS
├─ motorCalculo.py              # script que roda os códigos internos das pastas de dimensões para calcular os componentes de ISH
├─ requirements.txt             # pacotes requeridos no projeto
├─ dados_gerais/                # pasta com dados comuns a todas as dimensões (dataframe completo gerado pela função humana armazenado em arquivo .csv)
├─ output/                      # pasta onde ficam os resultados de joinISH.py
├─ functions_module_ish_*/      # padrão de pasta para cálculos de cada dimensão (a dimensão humana é o padrão; o padrão é functions_module_ish_hum)
|   ├─ input/                   # pasta com dados para serem base para o motor de Cálculo
|   ├─ output/                  # pasta da saída do valor final da dimensão feito pelo motor de Cálculo 
|   ├─ calcular_dimensao.py     # motor de Cálculo propriamente dito na pasta
|   ├─ convertion_functions.py  # biblioteca de funções utilizadas
|   ├─ comparar.py              # arquivo para comparar valores calculados e valores padronizados calculados anteriormente
├─ Metodologia_ISH_ANA.pdf      # origem teórica de medidas tomadas pela ANA
├─ Metodologia_ISH-LUNC.md      # origem teórica de medidas tomadas no projeto
├─ ISH-LUNC_fluxograma.svg      # imagem do fluxograma de funcionamento previsto para o projeto - TODO
└─ apresentacao/                # Pasta com geodataframes utilizados para gerar valores agregados por regiões
   └─ *.gpkg                    # Importante ser do tipo gpkg
```

---
