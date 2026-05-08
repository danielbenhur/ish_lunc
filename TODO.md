# Arquivo com Kanban detalhado de todas as tarefas que precisamos fazer e os pesos definidos por nós de qual tarefa é prioritária
Pesos:
- Urgência (referente à alguma meta que está próxima de vencer o prazo),
- Importância (da tarefa para o projeto como um todo);
- Facilidade de desenvolvimento.

Estrutura:
- Descrição da tarefa
- Responsável
- Estágio do desenvolvimento
- Quantidade de horas gastas
- Prioridade de acordo com os pesos pré-estabelecidos

# Missões Gerais:
- Estudo de desempenho entre GeoPandas e PyQGIS para elaboração de interface de elaboração de mapas;
- Desenvolvimento de interface de usuário para entrega de parâmetros para mapas;
- Código para importação de dados da fonte;
- Código para tratamento de dados e adequação de modelo;
- Adaptação de funções para modelo multicritério

# Atividades Específicas a fazer:
- Correção dos fatores calculados em código
    - Descrição da tarefa: correção da diferença entre os índices do modelo calculado e o parâmetro que estamos usando
    - Responsável: Luca
    - Estágio do desenvolvimento inicial: Já conseguimos calcular os índices e comparar com o modelo original; precisamos deixar claro o que é dado de saída e entrada e o motivo dos erros
    - Quantidade de horas gastas:
    - Prioridade de acordo com os pesos pré-estabelecidos: Urgência: baixa; Importância: média; Facilidade de desenvolvimento: alta; prioridade segunda

- Adequação do código para plugin do QGIS, incluindo entrega de parâmetros e detalhamento de pedido
    - Descrição da tarefa: Criação de plugin do QGIS que englobe tanto os scrips já feitos quanto entrada e saída que o usuário pedir
    - Responsável: Luca
    - Estágio do desenvolvimento inicial: zero
    - Quantidade de horas gastas:
    - Prioridade de acordo com os pesos pré-estabelecidos: Urgência: média; Importância: média; Facilidade de desenvolvimento: média; prioridade terceira

- Tabela que entregue indicadores com todos os dados juntos
    - Descrição da tarefa: Queremos uma tabela que entregue todos os indicadores juntos, não só os dados calculados, de modo que o mapa consiga traduzir esses indicadores tanto calculados quanto dados pelo projeto; precisamos que algum código consiga tratar os dados e entregar a tabela completa;
    - Parte 1: colocar pesos adequáveis para cada grandeza que afeta um índice geral do joinISH (mudar YAML para incluir pesos específicos);
    - Parte 2: integração de funções de todos os arquivos de script e de funções
    - Parte 3: adequação do código para leitura de yaml que chame funções ao invés de um paradigma estruturado (proposta: escrever uma função genérica que é moldada para servir na integração dos dados ou para ser chamada de maneira que o próprio usuário decida como vai ser essa função de maneira simples)
    - Responsável: Luca
    - Estágio do desenvolvimento inicial: temos alguns códigos que fazem tabelas a partir de dados específicos já entregues; o joinISH está trabalhando com cópias de arquivos prontos por códigos específicos e não faz as coisas diretamente;
    - Quantidade de horas gastas:
    - Prioridade de acordo com os pesos pré-estabelecidos: Urgência: alta; Importância: alta; Facilidade de desenvolvimento: média; prioridade primeira

# Atividades em andamento:
- Tabela que entregue indicadores com todos os dados juntos
    - Quantidade de horas gastas: 3h
    - Andamento: Os pesos adequados podem ser lidos por yaml (ainda precisa ser colocado em linha de código como aplicar, não tem uma função geral que integre tudo isso ainda)
# Atividades concluídas:
