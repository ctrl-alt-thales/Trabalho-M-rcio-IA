# app.py

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import re
import spacy
#import nltk
#from nltk.tokenize import word_tokenize

from sympy import symbols
from sympy.logic.boolalg import And, Or, Not, Implies, Equivalent
from sympy import sympify

# ----------------------------
# 1. INICIALIZAÇÃO GERAL
# ----------------------------

app = Flask(__name__)
CORS(app)  # aqui eu habilito CORS para aceitar requisições do HTML

# carrego modelo de português do spaCy
nlp = spacy.load("pt_core_news_sm")

# garanto que o NLTK tenha o tokenizador
#nltk.download("punkt", quiet=True)


# ----------------------------
# 2. FUNÇÕES AUXILIARES
# ----------------------------

def normalizar_texto_pt(texto: str) -> str:
    """
    Uso spaCy e NLTK só para fazer um pré-processamento simples:
    - deixar minúsculo
    - remover espaços extras
    - manter só o que interessa
    """
    texto = texto.strip()
    # analiso com spaCy (não vou usar tudo, mas já mostra o uso do modelo)
    doc = nlp(texto)
    tokens = [t.text for t in doc]
    texto_norm = " ".join(tokens).lower()

    # normaliza qualquer forma de 'não'
    texto_norm = texto_norm.replace(" nao ", " não ")
    texto_norm = texto_norm.replace(" ñao ", " não ")
    texto_norm = texto_norm.replace(" n˜ao ", " não ")
    texto_norm = texto_norm.replace(" năo ", " não ")
    texto_norm = texto_norm.replace(" nâo ", " não ")
    texto_norm = texto_norm.replace(" naõ ", " não ")

    # limpo espaços duplicados
    texto_norm = re.sub(r"\s+", " ", texto_norm)
    return texto_norm


def detectar_conectivo_principal(frase: str):
    """
    Identifica o conectivo principal na frase em português.
    Agora também trata 'mas' como conjunção (∧),
    seguindo a ideia do professor de que 'mas' é um 'e' lógico.
    Retorna (esquerda, conectivo, direita).
    """
    # normalizo espaços
    frase = re.sub(r"\s+", " ", frase.strip())

    # bicondicional
    if " se e somente se " in frase:
        left, right = frase.split(" se e somente se ", 1)
        return left, "↔", right

    # implicação
    if frase.startswith("se ") and " então " in frase:
        resto = frase[3:]
        left, right = resto.split(" então ", 1)
        return left, "→", right

    # conjunção adversativa 'mas' (tratada como ∧ na lógica)
    # exemplos: "X, mas Y" ou "X mas Y"
    if " mas " in frase:
        left, right = frase.split(" mas ", 1)
        return left, "∧", right

    # conjunção 'e'
    if " e " in frase:
        left, right = frase.split(" e ", 1)
        return left, "∧", right

    # disjunção 'ou'
    if " ou " in frase:
        left, right = frase.split(" ou ", 1)
        return left, "∨", right

    return frase, "", ""


def quebrar_em_atomicas(frase: str):
    """
    Quebra a frase em possíveis proposições atômicas.
    Aqui eu só uso ' e ' e ' ou ' para subdividir,
    e limpo vírgulas e pontos no final.
    """
    texto = re.sub(r"\s+", " ", frase.strip())
    partes = re.split(r"\s(e|ou)\s", texto)
    atomicas = []
    atual = ""
    for p in partes:
        if p in ("e", "ou"):
            if atual:
                atomicas.append(atual.strip())
            atual = ""
        else:
            if atual:
                atual += " " + p
            else:
                atual = p
    if atual:
        atomicas.append(atual.strip())

    # remove vírgulas/pontos no final
    atomicas_limpa = []
    for a in atomicas:
        a = a.strip()
        a = re.sub(r"[.,]+$", "", a)  # tira , e . do final
        atomicas_limpa.append(a.strip())
    return atomicas_limpa


def mapear_atomicas_para_letras(atomicas):
    """
    Gera um dicionário { 'P': 'texto da proposição' }.
    Se a atômica tiver 'não', eu guardo a versão POSITIVA no mapeamento.
    Ex.: 'kiki não é uma gata' -> mapeamento['Q'] = 'kiki é uma gata'
    """
    letras = list("PQRSTUVWXYZABCDEFGHIJKLMN")
    mapping = {}
    idx = 0
    for at in atomicas:
        txt = at.strip().lower()
        # remove vírgulas/pontos finais
        txt = re.sub(r"[.,]+$", "", txt).strip()

        # se tiver ' não ' no meio, guardo versão positiva
        if " não " in txt:
            # remove apenas o primeiro ' não '
            positivo = txt.replace(" não ", " ", 1)
            positivo = re.sub(r"\s+", " ", positivo).strip()
            base = positivo
        elif txt.startswith("não "):
            positivo = txt[4:]
            positivo = re.sub(r"\s+", " ", positivo).strip()
            base = positivo
        else:
            base = txt

        # evita duplicar o mesmo texto
        if base not in mapping.values():
            mapping[letras[idx]] = base
            idx += 1

    return mapping


def construir_formula_cpc(frase: str, mapping: dict) -> str:
    """
    Constrói uma fórmula em CPC a partir da frase normalizada e do mapeamento.
    Regras:
    - 'mas' vira ∧
    - 'não X' ou 'X não Y' vira ¬(proposição positiva)
    """
    frase = re.sub(r"\s+", " ", frase.strip().lower())
    frase = re.sub(r"[.,]+$", "", frase).strip()  # tira vírgula/ponto no final

    # caso 1: frase começa com 'não '
    if frase.startswith("não "):
        resto = frase[4:].strip()
        # procura a proposição positiva no mapping
        for letra, texto in mapping.items():
            if texto == resto:
                return f"¬{letra}"
        # se não achar, tenta recursivo
        inner = construir_formula_cpc(resto, mapping)
        return f"¬({inner})"

    # tenta achar conectivo principal
    left, conn, right = detectar_conectivo_principal(frase)
    if conn == "":
        # caso 2: frase atômica com ' não ' no meio
        if " não " in frase:
            # remove apenas o primeiro ' não '
            positivo = frase.replace(" não ", " ", 1)
            positivo = re.sub(r"\s+", " ", positivo).strip()
            for letra, texto in mapping.items():
                if texto == positivo:
                    return f"¬{letra}"
            # se não achar, tenta recursivo
            inner = construir_formula_cpc(positivo, mapping)
            return f"¬({inner})"

        # caso 3: frase atômica simples
        for letra, texto in mapping.items():
            if texto == frase:
                return letra
        raise ValueError(f"Frase atômica '{frase}' não mapeada para nenhuma letra.")

    # caso 4: temos conectivo (∧, ∨, →, ↔)
    f_left = construir_formula_cpc(left, mapping)
    f_right = construir_formula_cpc(right, mapping)
    return f"({f_left} {conn} {f_right})"


# ---------- SymPy: normalização e tradução ----------

def cpc_para_sympy(formula: str):
    """
    Converto a fórmula no estilo do professor para a sintaxe do SymPy.
    Exemplos aceitos: p^¬q, p∧q, p v q, p∨q, p->q, p→q, p<->q, p↔q
    """
    f = formula.replace(" ", "").lower()

    # troco conectivos pelo equivalente do SymPy
    f = f.replace("¬", "~")
    f = f.replace("~", "~")
    f = re.sub(r"(?<!~)!","~", f)  # se usar ! como negação

    f = f.replace("^", "&").replace("∧", "&")
    f = f.replace("v", "|").replace("∨", "|")

    f = f.replace("<->", ">>=")  # gambiarra temporária
    f = f.replace("↔", ">>=")
    f = f.replace("->", ">>")
    f = f.replace("→", ">>")

    # agora arrumo o bicondicional: uso Equivalent(a, b)
    if ">>=" in f:
        left, right = f.split(">>=", 1)
        return Equivalent(sympify(left), sympify(right))

    expr = sympify(f, evaluate=False)
    return expr


def expr_para_nl(expr, mapping: dict) -> str:
    """
    Converte um objeto SymPy (And, Or, Not, Implies, Equivalent, Symbol)
    para uma frase em português, usando o mapping das letras.
    """
    # símbolo atômico
    if expr.is_Symbol:
        letra = str(expr)
        return mapping.get(letra.upper(), mapping.get(letra, letra))

    if isinstance(expr, Not):
        return "não " + expr_para_nl(expr.args[0], mapping)

    if isinstance(expr, And):
        partes = [expr_para_nl(a, mapping) for a in expr.args]
        return " e ".join(partes)

    if isinstance(expr, Or):
        partes = [expr_para_nl(a, mapping) for a in expr.args]
        return " ou ".join(partes)

    if isinstance(expr, Implies):
        antecedente = expr_para_nl(expr.args[0], mapping)
        consequente = expr_para_nl(expr.args[1], mapping)
        return f"Se {antecedente}, então {consequente}"

    if isinstance(expr, Equivalent):
        left = expr_para_nl(expr.args[0], mapping)
        right = expr_para_nl(expr.args[1], mapping)
        return f"{left} se e somente se {right}"

    # fallback
    return str(expr)


# ----------------------------
# 3. ENDPOINTS DA API
# ----------------------------

@app.route("/api/nl-to-cpc", methods=["POST"])
def api_nl_to_cpc():
    """
    Espera JSON assim:
    {
      "frase": "Se chover, então a grama ficará molhada."
    }
    """
    data = request.get_json(force=True)  # pego o JSON que veio da página
    frase = data.get("frase", "").strip()

    if not frase:
        return jsonify({
            "ok": False,
            "erro": "O campo 'frase' é obrigatório."
        }), 400

    try:
        frase_norm = normalizar_texto_pt(frase)
        # extraio as possíveis atômicas para mapear em letras
        left, conn, right = detectar_conectivo_principal(frase_norm)
        atomicas = []
        if conn == "":
            atomicas = [frase_norm]
        else:
            atomicas.extend(quebrar_em_atomicas(left))
            atomicas.extend(quebrar_em_atomicas(right))

        atomicas = [a for a in atomicas if a]
        mapping = mapear_atomicas_para_letras(atomicas)
        formula = construir_formula_cpc(frase_norm, mapping)

        return jsonify({
            "ok": True,
            "frase_original": frase,
            "frase_normalizada": frase_norm,
            "formula_cpc": formula,
            "mapeamento": mapping
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "erro": str(e)
        }), 500


@app.route("/api/cpc-to-nl", methods=["POST"])
def api_cpc_to_nl():
    """
    Espera JSON assim:
    {
      "formula": "p^¬q",
      "mapeamento": {
        "p": "Gatos comem de tudo",
        "q": "Kiki é uma gata"
      }
    }
    """
    data = request.get_json(force=True)
    formula = data.get("formula", "").strip()
    mapping = data.get("mapeamento", {})

    if not formula:
        return jsonify({
            "ok": False,
            "erro": "O campo 'formula' é obrigatório."
        }), 400

    if not isinstance(mapping, dict) or not mapping:
        return jsonify({
            "ok": False,
            "erro": "O campo 'mapeamento' deve ser um dicionário com as letras."
        }), 400

    try:
        expr = cpc_para_sympy(formula)
        frase_nl = expr_para_nl(expr, mapping)

        return jsonify({
            "ok": True,
            "formula_original": formula,
            "mapeamento": mapping,
            "frase_nl": frase_nl
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "erro": str(e)
        }), 500
    

@app.route("/")
def raiz():
    # Em produção (ex.: Render), esta rota serve o arquivo index.html
    # que está no mesmo diretório do app.py
    return send_from_directory(".", "index.html")


if __name__ == "__main__":
    # Em produção (Render), a porta vem da variável de ambiente PORT.
    # Localmente, usamos 5000 como padrão.
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
