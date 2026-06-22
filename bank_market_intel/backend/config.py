"""Configuração dos bancos e métricas suportadas via BCB IF.data."""

BCB_IFDATA_BASE = "https://olinda.bcb.gov.br/olinda/servico/IFDATA/versao/v1/odata"

# Conglomerados prudenciais (TipoInstituicao=1) no IF.data
BANKS = {
    "itau": {
        "name": "Itaú",
        "cod_inst": "C0080099",
        "color": "#EC7000",
    },
    "bradesco": {
        "name": "Bradesco",
        "cod_inst": "C0080075",
        "color": "#CC092F",
    },
    "bb": {
        "name": "BB",
        "cod_inst": "C0080329",
        "color": "#F8D117",
    },
    "santander": {
        "name": "Santander",
        "cod_inst": "C0080185",
        "color": "#EC0000",
    },
    "nubank": {
        "name": "Nubank",
        "cod_inst": "C0084693",
        "color": "#8A05BE",
    },
}

# Relatório 1 = Resumo (BCB usa número, não o nome)
REPORT_RESUMO = "1"

# Colunas exatas no IF.data (relatório Resumo)
COL_LUCRO = "Lucro Líquido"
COL_BASILEIA = "Índice de Basileia"
COL_PL = "Patrimônio Líquido"

HISTORY_START = 202303  # 1T23 — início do histórico exibido
