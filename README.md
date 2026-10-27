# Raiz — inteligência territorial do agro

**[Abrir painel / Open dashboard / 打开面板](https://edilvando.github.io/raiz-agro-intelligence/)** · [Edilvando Eufrazio](https://www.linkedin.com/in/edilvando-eufrazio-49b63417/)

Um painel para transformar a **estrutura observada no Censo Agropecuário 2017** em hipóteses de expansão e pilotos comerciais. Interface completa em **Português, English e 简体中文**, com mapa, ranking ajustável, grupos exploratórios, mix produtivo e simulador.

> Base histórica de 2017. Triagem territorial em nível estadual, sem comprovação de demanda atual, previsão de receita ou contatos de produtores. Projeto pessoal independente, sem endosso institucional.

## Caso guiado — três territórios para um piloto

[Abrir o exemplo em português](https://edilvando.github.io/raiz-agro-intelligence/piloto-agtech.html).

Uma agtech hipotética usa a triagem nacional para propor PR, SC e RS para um piloto regional de 90 dias. O exemplo mostra alternativas, empates, sensibilidade dos pesos, orçamento incremental e critérios de medição. Dados observados são de 2017; empresa, metas e custos são premissas ilustrativas. Todos os resultados de campo permanecem nulos.

Reprodução adicional na distribuição GitHub: `node build_case.cjs` e `python3 validate_case.py`. No checkout estruturado: `node scripts/build_case.cjs` e `python3 scripts/validate_case.py`. O validador refaz percentis e posições com frações exatas e concilia as contagens com os arquivos brutos. A página do caso está em português; o painel permanece nos três idiomas.

## Usos para empresas

| Missão | Base observada | Próxima validação |
|---|---|---|
| Tecnologia e conectividade | Estabelecimentos com internet | Adoção atual, integração, uso e pagamento |
| Assistência e insumos | Estabelecimentos sem orientação técnica | Necessidade agronômica, canal e intenção de contratar |
| Máquinas e pós-venda | Estabelecimentos com tratores | Idade da frota, peças, manutenção e renovação |

Ajuste o peso entre **volume** e **intensidade** e veja como o top 5 responde a ±20 pontos percentuais. Selecione uma UF no mapa, ranking, gráfico de bolhas ou tabela. O recorte regional filtra a comparação; a referência dos percentis permanece nas 27 UFs.

O simulador parte da base histórica selecionada e aplica **premissas ilustrativas editáveis** de alcance, conversão, ticket mensal, capacidade e custo por contato. Mostra contatos, clientes equivalentes, receita mensal hipotética e custo de prospecção. Todos os valores monetários permanecem em BRL em qualquer idioma.

## Evidências que mudam a leitura

- O Brasil registrou **5.073.324 estabelecimentos**, dos quais **1.430.156 com internet** e **1.025.443 com orientação técnica**.
- **734.280 estabelecimentos tinham tratores**, somando **1.229.907 tratores**. Estabelecimentos e máquinas são medidas diferentes.
- Em Mato Grosso, **aproximadamente 80% dos estabelecimentos** tinham pecuária e criação de outros animais como atividade principal. Isso mede estabelecimentos, não participação na área, produção ou receita. Associar automaticamente o estado apenas aos grãos pode levar a um canal comercial inadequado.
- Dois grupos foram escolhidos pela maior silhueta entre as soluções elegíveis. A segmentação descreve semelhanças; não estima propensão a comprar.

## Ciência de dados, sem caixa-preta

**Priorização multicritério:** percentil de volume × peso + percentil da taxa × (1 − peso). Empates usam posto médio. É uma regra de triagem configurável, sem calibração comercial ou interpretação probabilística.

**Segmentação:** k-means++ implementado em Python padrão, distância euclidiana, z-score de cinco atributos: taxa de internet, orientação técnica, posse de tratores, agricultura familiar e log(1 + área média). Busca k=2…5, com 40 inicializações por k. A solução elegível de menor inércia precisa ter pelo menos 3 UFs por grupo. Escolha final pela maior silhueta: **k=2, silhueta ≈0,437**. N=27 observações agregadas; solução exploratória, sem validação externa ou inferência causal. Cartões mostram médias **não ponderadas** das taxas estaduais.

**Interseções desconhecidas:** internet e ausência de assistência vêm de margens separadas. O painel apresenta limites de Fréchet, `max(0,A+B−N)` a `min(A,B)`, em vez de presumir independência multiplicando taxas.

## Fonte e reprodutibilidade

SIDRA/IBGE, resultados definitivos de 2017: [6753](https://sidra.ibge.gov.br/tabela/6753), [6778](https://sidra.ibge.gov.br/tabela/6778), [6846](https://sidra.ibge.gov.br/tabela/6846), [6871](https://sidra.ibge.gov.br/tabela/6871) e [6962](https://sidra.ibge.gov.br/tabela/6962). Malha estadual simplificada e cadastro de UFs: API oficial do IBGE. Extração em **27/10/2026**; data de extração não altera o ano de referência.

Cada arquivo bruto tem URL, horário e SHA-256 em `manifest.json` (distribuição GitHub) ou `data/raw/manifest.json` (checkout estruturado). O build verifica os hashes antes de gerar dados e painel. Nulos/suprimidos permanecem nulos; o traço do SIDRA representa zero absoluto. A execução atual tem cobertura completa dos indicadores usados.

### Distribuição GitHub (arquivos na raiz)

Os arquivos-fonte, os dados fixados e os testes ficam diretamente na raiz para facilitar a publicação pelo navegador, sem credenciais de terminal. O mesmo código também suporta a estrutura local `scripts/`, `web/`, `data/`, `tests/` e `docs/`.

```sh
python3 build.py
python3 -m unittest discover -s . -p 'test_data.py' -v
node --check app.js
node --test test_models.cjs
python3 -m http.server 8000 --bind 127.0.0.1
```

No checkout estruturado, use `python3 scripts/build.py`, `python3 -m unittest discover -s tests -v`, `node --test tests/test_models.cjs` e abra `docs/index.html`.

Python e Node sem dependências adicionais. Chart.js 4.5.1 incluído localmente, com a licença original em `Chartjs-LICENSE.md`. Fonte web opcional; na ausência de internet, a interface usa fontes do sistema. Dados e gráficos funcionam offline. `fetch_data.py` recusa sobrescrever um manifesto existente: renove a base em uma cópia nova e revise o novo snapshot.

**Validação:** 10 reconciliações de totais estaduais contra Brasil, partições de internet/assistência/atividade, 12 hashes e 27 geometrias; 6 testes Python e 7 testes Node. Áreas publicadas arredondadas: tolerância máxima de 27 ha; contagens exigem igualdade exata. Testes de ranking, limites de interseção, capacidade, CAC, nulos e idiomas.

## English

A reproducible, multilingual territorial screening tool for agribusiness, built from Brazil’s official **2017 Agricultural Census**. Explore state profiles, adjustable priorities, exploratory clusters and user-defined commercial pilot scenarios. This is a historical structural screen, not a current market estimate or sales forecast. Source geography names remain in their official Portuguese spelling; numbers, charts, controls and analytical explanations follow the selected interface language.

## 简体中文

本项目使用巴西官方**2017年农业普查**数据，为农业企业提供可复现的州级地区初筛工具。功能包括交互地图、可调优先级、探索性分群、生产结构以及用户自定义的商业试点情景。数据反映历史结构，并非当前市场规模估计，也不是销售预测。地区名称保留官方葡萄牙语拼写；界面、图表、数值格式及分析说明支持中文。

## Contato / Contact / 联系

[LinkedIn — Edilvando Eufrazio](https://www.linkedin.com/in/edilvando-eufrazio-49b63417/) · [GitHub — edilvando](https://github.com/edilvando)
