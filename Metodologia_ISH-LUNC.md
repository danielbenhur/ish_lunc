Metodologia de Cálculo do Índice de Segurança Hídrica LabGest-UFES/Neades-CPID (ISH-LUNC)
O Índice de Segurança Hídrica LabGest-UFES/Neades-CPID (ISH-LUNC), também denominado ISHNCLU ou ISH ajustado (ISHajustado)
, é um modelo analítico desenvolvido a partir do aprimoramento do Índice de Segurança Hídrica (ISH) original da Agência Nacional de Águas e Saneamento Básico (ANA)
.
O ISH-LUNC foi criado para ser mais aderente à realidade regional/local, ao incluir fatores que não estavam presentes na estrutura analítica do modelo base, como o risco de inundações
.
1. Estrutura do Índice e Indicadores
O ISH-LUNC é classificado como um modelo baseado em indicadores, utilizável em Sistemas de Informações Geográficas (SIG)
. Ele mantém as quatro dimensões originais do ISH, mas modifica a dimensão de resiliência, totalizando cinco componentes ou subdimensões consideradas no cálculo global
:
Dimensão/Subdimensão
	
Indicadores Principais
Humana
	
Garantia de água para abastecimento; Cobertura da rede de abastecimento
.
Econômica
	
Garantia de água para irrigação e pecuária; Garantia de água para atividade industrial
.
Ecossistêmica
	
Quantidade adequada de água para usos naturais; Qualidade adequada de água para usos naturais; Segurança de barragens de rejeito de mineração
.
Resiliência às Secas
	
Reservação artificial; Reservação Natural; Potencial de armazenamento subterrâneo; Variabilidade pluviométrica
.
Resiliência às Inundações
	
Vulnerabilidade às inundações (indicador único: IVI - Índice de Vulnerabilidade a Inundações da ANA)
.
A adição da subdimensão Resiliência às Inundações é a principal adaptação em relação ao ISH original, visando uma representação mais abrangente dos riscos relacionados à água, incluindo cheias e secas, em consonância com as definições da UN-Water (2013) e da ANA (2019c)
.
2. Cálculo do Índice no Nível Base
O ISH-LUNC é originalmente calculado por ottobacias
. Ottobacias são subdivisões de bacias hidrográficas, baseadas no método de codificação de cursos d'água de Otto Pfastetter, e representam o nível de maior detalhamento espacial do índice
.
O grau de segurança hídrica global do ISH-LUNC é obtido pela média simples dos valores não nulos do conjunto de suas cinco dimensões e subdimensões
:
ISH-LUNC=k∑i=1k​i​ (Equac¸​a˜o 4.1)
Onde:
• i = o valor da dimensão ou subdimensão
;
• k = o número total das dimensões (Humana, Econômica e Ecossistêmica) e subdimensões (Resiliência às Secas e Resiliência às Inundações) que sejam não nulas
. O valor máximo de k é 5
.
As dimensões são classificadas em cinco graus de segurança hídrica, variando de 1 (Mínimo) a 5 (Máximo)
.
3. Representação em Outros Recortes Regionais
Embora o cálculo base seja realizado por ottobacias, o ISH-LUNC pode ser representado em outros recortes regionais (como municípios, estados ou outras regiões hidrográficas)
.
A representação para recortes regionais diferentes das ottobacias se dá por meio de um processo de agregação
. A metodologia utiliza scripts de agregação que calculam a média (ou outras estatísticas, como máximo e mínimo)
dos resultados do ISH-LUNC das ottobacias.
A agregação é realizada por meio da média ponderada dos valores das ottobacias, considerando a área interceptada entre a ottobacia e a unidade de apresentação (recorte regional)
. Para este fim, são utilizados valores não nulos nas áreas interceptadas para calcular a média ponderada, garantindo que o índice agregado reflita o grau de segurança hídrica nas regiões de interesse
.
--------------------------------------------------------------------------------
Em termos práticos, imagine que a segurança hídrica do estado é um mosaico composto por milhares de pequenos ladrilhos (as ottobacias), e cada ladrilho tem uma cor que representa seu grau de segurança. O ISH-LUNC calcula a cor de cada ladrilho individualmente. Para saber a "cor média" de uma região maior, como um município, a agregação funciona como pesar a cor de cada ladrilho com base no tamanho da área que esse ladrilho cobre dentro dos limites daquele município.
