# Metodologia de Cálculo do Índice de Segurança Hídrica LabGest-UFES/Neades-CPID (ISH-LUNC)

O **Índice de Segurança Hídrica LabGest-UFES/Neades-CPID (ISH-LUNC)**, é um índice analítico desenvolvido a partir do aprimoramento do Índice de Segurança Hídrica (ISH) original da Agência Nacional de Águas e Saneamento Básico (ANA).

O ISH-LUNC foi criado para ser mais aderente à realidade regional/local do Espírito Santo, ao incluir fatores que não estavam presentes na estrutura analítica do índice base, como o risco de inundações. O ISH-LUNC está em constante aprimoramento, através de projetos realizados com coordenação do LabGest (Laboratório de Gestão de Recursos Hídricos e Desenvolvimento Regional), sediado na Universidade Federal do Espírito Santo (UFES) e do Núcleo Estratégico em Água e Desenvolvimento (Neades), sediado no Centro de Pesquisa, Inovação e Desenvolvimento do Espírito Santo (CPID).

O ISH-LUNC faz parte de um modelo em desenvolvimento no "Projeto Segurança Hídrica (SH) & Desenvolvimento Regional Sustentável (DRS)", realizado junto com setores importantes para a segurança hídrica do Espírito Santo. Como base desse projeto, defini-se que: 
> *A segurança hídrica é o grau de atendimento, de forma sustentável, às necessidades hídricas acordadas, acompanhado de um nível aceitável de risco de falhas no atendimento.*


## 1. Estrutura do Índice e Indicadores

O ISH-LUNC é classificado como um modelo baseado em indicadores. Ele mantém as quatro dimensões originais do ISH, mas modifica a dimensão de resiliência, dividindo-a em uma subdimensão de resiliência às secas e outra de resiliência às inundações, totalizando **cinco componentes** consideradas no cálculo global:

| Dimensão/Subdimensão | Indicadores Principais |
| :--- | :--- |
| **Humana** | Garantia de água para abastecimento; Cobertura da rede de abastecimento. |
| **Econômica** | Garantia de água para irrigação e pecuária; Garantia de água para atividade industrial. |
| **Ecossistêmica** | Quantidade adequada de água para usos naturais; Qualidade adequada de água para usos naturais; Segurança de barragens de rejeito de mineração. |
| **Resiliência às Secas** | Reservação artificial; Reservação Natural; Potencial de armazenamento subterrâneo; Variabilidade pluviométrica. |
| **Resiliência às Inundações** | Vulnerabilidade às inundações (indicador único: IVI - Índice de Vulnerabilidade a Inundações da ANA). |

A adição da subdimensão **Resiliência às Inundações** é a principal adaptação em relação ao ISH original, visando uma representação mais abrangente dos riscos relacionados à água, incluindo cheias e secas, em consonância com definições de segurança hídrica amplamente usadas internacionalmente (como a de UN-Water, 2013) e nacionalmente (como a da ANA, 2019). Outras alterações em relação ao ISH desenvolvido pela ANA corresponde à atualização da base de dados, reconstrução da metodologia e maior possibilidade de cálculo do índice para diferentes anos e cenários.

## 2. Cálculo do Índice

O ISH-LUNC é **originalmente calculado por ottobacias**. Ottobacias são subdivisões de bacias hidrográficas, baseadas no método de codificação de cursos d'água de Otto Pfastetter, e representam o nível de maior detalhamento espacial do índice.

O grau de segurança hídrica global do ISH-LUNC é obtido pela **média simples** dos valores não nulos do conjunto de suas cinco dimensões e subdimensões por ottobacia:

$$\text{ISH-LUNC}= \frac{\sum_{i=1}^{k} i}{k}$$

Onde:

*   $i$ = o valor da dimensão ou subdimensão;
*   $k$ = o número total das dimensões (Humana, Econômica e Ecossistêmica) e subdimensões (Resiliência às Secas e Resiliência às Inundações) que sejam **não nulas**. O valor máximo de $k$ é 5.

As dimensões são classificadas em cinco graus de segurança hídrica, variando de 1 (Mínimo) a 5 (Máximo).

## 3. Representação em Outros Recortes Regionais

Embora o cálculo base seja realizado por ottobacias, o ISH-LUNC pode ser representado em **outros recortes regionais** (como municípios, estados ou outras regiões hidrográficas).

A representação para recortes regionais diferentes das ottobacias se dá por meio de um processo de **agregação**. A metodologia utiliza scripts de agregação que calculam a média (ou outras estatísticas, como mediana, máxima e mínima) dos resultados do ISH-LUNC das ottobacias.

A agregação apresentada especificamente no Adapta ES é realizada pela **mediana** dos valores das ottobacias, considerando a **área interceptada** entre a ottobacia e a unidade de apresentação (recorte regional). Para este fim, são utilizados **valores não nulos de grau de segurança hídrica** nas áreas interceptadas para calcular a mediana. Através da mediana, destaque maior é dado para um cenário crítico, útil em termos de adaptação climática.

---
*Outras informações sobre a metodologia podem ser encontradas em:* 
- OLIVEIRA, D. B. H. S., VANELI, B. P., & TEIXEIRA, E. C. (2024). Aprimoramento do Índice de Segurança Hídrica da ANA: adição do indicador vulnerabilidade a inundações e aplicação na região hidrográfica do rio Jucu, ES - Brasil. Revista de Gestão de Água da América Latina, 21, e15. Disponível em: https://doi.org/10.21168/rega.v21e15
- OLIVEIRA, D. B. H. S. Aprimoramento da modelagem para avaliação de segurança hídrica no contexto do desenvolvimento regional.  sustentável. Dissertação de mestrado. Programa de Pós Graduação em Engenharia Ambiental - UFES. Disponível em: http://repositorio.ufes.br/handle/10/17419
- OLIVEIRA, D. B. H. S. ISH_LUNC. Github. Disponível em: https://github.com/danielbenhur/ish_lunc/

*Referências citadas*
- AGÊNCIA NACIONAL DE ÁGUA (ANA). Plano Nacional de Segurança Hídrica. ANA. Brasília, 2019. 112 p. ISBN: 978-85-8210-059-2. Disponível em: http://arquivos.ana.gov.br/pnsh/pnsh.pdf
- UN-WATER. Water security and the global water agenda: a UN-water analytical brief. Ontario: United Nations University - Institute for Water, Environment and Health, 2013. Disponível em: https://www.unwater.org/publications/water-security-and-global-water-agenda
