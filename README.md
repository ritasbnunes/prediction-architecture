# EcoFusion - Previsão de Custo, Duração e Emissões em Viagens Corporativas

Repositório de suporte ao estágio curricular realizado no **GECAD** no âmbito do Projeto-Estágio de Inteligência Artificial e Ciência de Dados.

O projeto desenvolve um sistema de previsão simultânea de três targets para voos domésticos nos EUA:
- **Custo** por passageiro (USD)
- **Duração real** do voo (minutos)
- **Emissões de CO₂** por voo (kg)

A arquitetura baseia-se num ensemble de stacking de dois níveis com validação walk-forward temporal (5 folds), integrado na plataforma EcoFusion para apoio à decisão em viagens corporativas sustentáveis.

---

## Estrutura do repositório

```
eco_fusion/
├── initial_validation_of_the_architecture/   # Fase 0 - exploração inicial com datasets públicos
├── benchmark_cost/                           # Fase 1a - replicação de Wong et al. (2023)
├── benchmark_duration/                       # Fase 1b - replicação de Biswas et al. (2024)
├── benchmark_emissions/                      # Fase 1c - validação da fórmula ICAO
├── generate_dataset/                         # Fase 2 - construção do dataset central BTS
├── architecture_implementation/
│   ├── without_external_features/            # Fase 3a - stacking sem features externas
│   └── with_external_features/               # Fase 3b - stacking com features externas
├── sensivity_analysis/                       # Fase 4 - análise de sensibilidade
└── export_final_model/                       # Fase 5 - exportação do modelo final
```

---

## Descrição das pastas

### `initial_validation_of_the_architecture/`
Teste exploratório inicial da arquitetura proposta com datasets públicos (voos, aeroportos, preços de combustível, taxas de câmbio e eventos de conflito). Serve para validar a viabilidade da abordagem antes de usar os dados BTS reais.

### `benchmark_cost/`
Replicação de [Wong et al. (2023)](https://arxiv.org/abs/2310.07787) para previsão de `baseFare` em voos domésticos non-stop com o dataset Expedia/Kaggle. Treina e avalia Random Forest, Gradient Boost Tree, Decision Tree e Factorization Machines (proxy sklearn). O modelo RF resultante (`modelo_custo_rf.pkl`) é usado na fase seguinte para imputar custos no dataset BTS.

### `benchmark_duration/`
Replicação de Biswas et al. (2024) para previsão da duração do voo. Contém dois notebooks:
- `notebook_duracao_a.ipynb` - versão com data leakage (DISTANCE_ARR_DELAY incluída), para comparação
- `notebook_duracao_b.ipynb` - versão corrigida sem data leakage, usada nos resultados finais

### `benchmark_emissions/`
Validação da fórmula física ICAO adaptada:
```
CO₂_kg = (distância_haversine + 95) × 4,5 × 3,16
```
Confronta os valores estimados com os dados reais de consumo de combustível do BTS Form 41 P-12(a) por quota de mercado de cada companhia aérea (MAE = 1,07 p.p.).

### `generate_dataset/`
Constrói o dataset central de 195 950 voos BTS 2023 (Jan–Ago, 5 estados: CA, TX, FL, NY, GA) com os três targets integrados:
- Custo imputado por RF → generalizado com LightGBM + ruído N(0, 35²)
- Duração calculada como `CRS_ELAPSED_TIME + ARR_DELAY − DEP_DELAY`
- CO₂ pela fórmula ICAO com fator de eficiência por companhia

Produz `generated_dataset.csv` (29 colunas, ~40 MB).

### `architecture_implementation/without_external_features/`
**Fase 3a** - Arquitetura de stacking multi-target sem features externas:
- Seleção de features por votação (Pearson + LASSO + RF importance, ≥ 2 votos)
- Nível 0: modelos base (LR, RF, XGB para custo; RF, LinearSVR, XGB para duração; ICAO, RF, XGB para CO₂)
- Nível 1: Ridge com cross-target features (previsão dos outros dois targets como input)
- Walk-forward 5 folds temporais
- Interpretabilidade SHAP e camada de cenários operacionais

Contém também `generate_new_dataset.ipynb`, que enriquece o dataset base com features externas (preço de combustível EIA, preço de carbono CARB, load factor BTS T-100, feriados federais, clima ERA5 via Open-Meteo), produzindo `generated_dataset_ext.csv`.

### `architecture_implementation/with_external_features/`
**Fase 3b** - Mesma arquitetura da Fase 3a com 17 features externas candidatas. A seleção final inclui `load_factor_prev_month` e `hist_route_price` para o custo, e variáveis climáticas para a duração. CO₂ não recebe features externas por razões de causalidade física.

### `sensivity_analysis/`
Análise de sensibilidade one-at-a-time sobre a Fase 3b. Testa 7 configurações variando o `alpha` do Ridge (0,1 e 10,0), o `n_estimators` do RF (50 e 200) e o limiar de Pearson (0,01 e 0,05). Conclui que a arquitetura é robusta ao custo e à duração; o CO₂ é o target mais sensível.

### `export_final_model/`
Exporta o modelo completo da Fase 3b para um ficheiro `prediction_model.joblib` através da classe `EcoFusionPredictor`. O predictor encapsula os scalers, encoders, modelos de Nível 0 (treinados com todo o histórico) e os Ridge de Nível 1 (calibrados com OOF), prontos para receber um `DataFrame` com novos voos.

---

## Ordem de execução

Os notebooks devem ser executados na seguinte sequência. Os datasets necessários (ver secção abaixo) devem ser colocados na mesma pasta do notebook antes de correr.

| Passo | Notebook | Produz |
|---|---|---|
| 0 | `initial_validation_of_the_architecture/01_test_public_datasets.ipynb` | Exploração inicial (opcional) |
| 1a | `benchmark_cost/notebook_custo.ipynb` | `modelo_custo_rf.pkl`, `encoders_custo.pkl` |
| 1b | `benchmark_duration/notebook_duracao_a.ipynb` | Benchmark duração (com leakage) |
| 1b | `benchmark_duration/notebook_duracao_b.ipynb` | `nb02_duration_output.csv` |
| 1c | `benchmark_emissions/notebook_emissoes.ipynb` | `nb03_co2_output.csv` |
| 2 | `generate_dataset/generated_dataset.ipynb` | `generated_dataset.csv` |
| 2b | `architecture_implementation/with_external_features/generate_new_dataset.ipynb` | `generated_dataset_ext.csv` |
| 3a | `architecture_implementation/without_external_features/notebook_3a.ipynb` | Resultados Fase 3a + figuras |
| 3b | `architecture_implementation/with_external_features/notebook_3b.ipynb` | Resultados Fase 3b + figuras |
| 4 | `sensivity_analysis/sensitivity_analysis.ipynb` | Resultados de sensibilidade |
| 5 | `export_final_model/final_model_export.ipynb` | `prediction_model.joblib` |

---

## Requisitos

```bash
pip install pandas numpy matplotlib seaborn scikit-learn xgboost lightgbm shap joblib openmeteo-requests requests-cache retry-requests
```

Python ≥ 3.9 recomendado.

---

## Dados necessários (não incluídos no repositório)

Os ficheiros de dados brutos não estão incluídos no repositório devido ao seu tamanho. Devem ser descarregados e colocados na pasta indicada antes de executar o notebook correspondente.

| Ficheiro | Pasta | Fonte | Utilização |
|---|---|---|---|
| `itineraries.csv` (~29 GB) | `benchmark_cost/` | [Kaggle - dilwong/flightprices](https://www.kaggle.com/datasets/dilwong/flightprices) | Benchmark custo (Expedia 2022) |
| Dados BTS On-Time Performance 2023 (CA, TX, FL, NY, GA) | `benchmark_duration/` e `benchmark_emissions/` | [BTS TranStats](https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ) | Dataset principal de voos |
| `T_F41SCHEDULE_P12A.csv` | `benchmark_emissions/` | [BTS Form 41 - P-12(a)](https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=G) | Validação consumo de combustível |
| `T_T100D_SEGMENT_ALL_CARRIER.csv` | `architecture_implementation/with_external_features/` | [BTS T-100 Domestic Segment](https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FHK) | Load factor mensal por companhia |
| `PET_PRI_SPT_S1_D.xls` | `architecture_implementation/with_external_features/` | [EIA - Petroleum Prices](https://www.eia.gov/dnav/pet/pet_pri_spt_s1_d.htm) | Preço do combustível de aviação |
| `nc-allowance_prices.csv` | `architecture_implementation/with_external_features/` | [CARB - Cap-and-Trade](https://ww2.arb.ca.gov/our-work/programs/cap-and-trade-program/auction-information) | Preço de carbono (USD/tCO₂) |

Os dados climáticos (temperatura, precipitação, vento) são descarregados automaticamente via API Open-Meteo ERA5 dentro do notebook `generate_new_dataset.ipynb`.

---

## Resultados principais (Fase 3b - com features externas)

| Target | RMSE | R² | Benchmark de referência |
|---|---|---|---|
| Custo (USD) | 39,17 | 68,84% | Wong et al. (2023) - R²=0,728 |
| Duração (min) | 14,01 | 96,31% | Biswas et al. (2024) - RMSE=1,67 min* |
| CO₂ (kg) | 95,95 | 99,995% | Fórmula ICAO (validação física) |

*os RMSE não são diretamente comparáveis.
