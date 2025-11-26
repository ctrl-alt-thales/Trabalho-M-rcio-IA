# app.py

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import re
import spacy
from sympy import symbols
from sympy.logic.boolalg import And, Or, Not, Implies, Equivalent
from sympy import sympify


app = Flask(__name__)
CORS(app)


# ---------------------------------------------------
#  Carregar spaCy com fallback caso não esteja instalado
# ---------------------------------------------------
try:
    nlp = spacy.load("pt_core_news_sm")
except Exception:
    # fallback simples para não quebrar o Render
    import os
    os.system("python -m spacy download pt_core_news_sm")
    nlp = spacy.load("pt_core_news_sm")


# ---------------------------------------------------
# 1) Normalização
# ---------------------------------------------------
def normalizar_texto_pt(texto: str) -> str:
    texto_norm = texto.lower().strip()
    texto_norm = re.sub(r"\s+", " ", texto_norm)
    return texto_norm

# ---------------------------------------------------
# 2) Conectivos
# ---------------------------------------------------
def detectar_conectivo_principal(frase: str):
    frase = re.sub(r"\s+", " ", frase.strip())

    if " se e somente se " in frase:
        left, right = frase.split(" se e somente se ", 1)
        return left, "↔", right

    if frase.startswith("se ") and " então " in frase:
        resto = frase[3:]
        left, right = resto.split(" então ", 1)
        return left, "→", right

    if " mas " in frase:
        left, right = frase.split(" mas ", 1)
        return left, "∧", right

    if " e " in frase:
        left, right = frase.split(" e ", 1)
        return left, "∧", right

    if " ou " in frase:
        left, right = frase.split(" ou ", 1)
        return left, "∨", right

    return frase, "", ""


# ---------------------------------------------------
# 3) Atomização
# ---------------------------------------------------
def quebrar_em_atomicas(frase: str):
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

    atomicas_limpa = [re.sub(r"[.,]+$", "", a.strip()) for a in atomicas]

    return atomicas_limpa


# ---------------------------------------------------
# 4) Mapear proposições → letras
# ---------------------------------------------------
def mapear_atomicas_para_letras(atomicas):
    letras = list("PQRSTUVWXYZABCDEFGHIJKLMN")
    mapping = {}
    idx = 0

    for at in atomicas:
        txt = at.strip().lower()
        txt = re.sub(r"[.,]+$", "", txt).strip()

        if " não " in txt:
            positivo = txt.replace(" não ", " ", 1)
        elif txt.startswith("não "):
            positivo = txt[4:]
        else:
            positivo = txt

        positivo = re.sub(r"\s+", " ", positivo).strip()

        if positivo not in mapping.values():
            mapping[letras[idx]] = positivo
            idx += 1

    return mapping


# ---------------------------------------------------
# 5) Construir fórmula CPC
# ---------------------------------------------------
def construir_formula_cpc(frase: str, mapping: dict) -> str:
    frase = re.sub(r"\s+", " ", frase.strip().lower())
    frase = re.sub(r"[.,]+$", "", frase)

    if frase.startswith("não "):
        resto = frase[4:].strip()
        for letra, texto in mapping.items():
            if texto == resto:
                return f"¬{letra}"
        inner = construir_formula_cpc(resto, mapping)
        return f"¬({inner})"

    left, conn, right = detectar_conectivo_principal(frase)

    if conn == "":
        if " não " in frase:
            positivo = frase.replace(" não ", " ", 1)
            positivo = re.sub(r"\s+", " ", positivo).strip()
            for letra, texto in mapping.items():
                if texto == positivo:
                    return f"¬{letra}"
            inner = construir_formula_cpc(positivo, mapping)
            return f"¬({inner})"

        for letra, texto in mapping.items():
            if texto == frase:
                return letra

        raise ValueError(f"Frase atômica '{frase}' não mapeada.")

    f_left = construir_formula_cpc(left, mapping)
    f_right = construir_formula_cpc(right, mapping)
    return f"({f_left} {conn} {f_right})"


# ---------------------------------------------------
# 6) CPC → SymPy
# ---------------------------------------------------
def cpc_para_sympy(formula: str):
    f = formula.replace(" ", "").lower()
    f = f.replace("¬", "~")
    f = f.replace("^", "&").replace("∧", "&")
    f = f.replace("v", "|").replace("∨", "|")
    f = f.replace("<->", "↔")
    f = f.replace("->", "→")

    if "↔" in f:
        left, right = f.split("↔", 1)
        return Equivalent(sympify(left), sympify(right))

    if "→" in f:
        left, right = f.split("→", 1)
        return Implies(sympify(left), sympify(right))

    return sympify(f, evaluate=False)


# ---------------------------------------------------
# 7) SymPy → NL
# ---------------------------------------------------
def expr_para_nl(expr, mapping):
    if expr.is_Symbol:
        return mapping.get(str(expr).upper(), str(expr))

    if isinstance(expr, Not):
        return "não " + expr_para_nl(expr.args[0], mapping)

    if isinstance(expr, And):
        return " e ".join(expr_para_nl(a, mapping) for a in expr.args)

    if isinstance(expr, Or):
        return " ou ".join(expr_para_nl(a, mapping) for a in expr.args)

    if isinstance(expr, Implies):
        return f"Se {expr_para_nl(expr.args[0], mapping)}, então {expr_para_nl(expr.args[1], mapping)}"

    if isinstance(expr, Equivalent):
        return f"{expr_para_nl(expr.args[0], mapping)} se e somente se {expr_para_nl(expr.args[1], mapping)}"

    return str(expr)


# ---------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------
@app.route("/api/nl-to-cpc", methods=["POST"])
def api_nl_to_cpc():
    data = request.get_json(force=True)
    frase = data.get("frase", "").strip()

    if not frase:
        return jsonify({"ok": False, "erro": "O campo 'frase' é obrigatório."}), 400

    try:
        frase_norm = normalizar_texto_pt(frase)
        left, conn, right = detectar_conectivo_principal(frase_norm)

        if conn == "":
            atomicas = [frase_norm]
        else:
            atomicas = quebrar_em_atomicas(left) + quebrar_em_atomicas(right)

        mapping = mapear_atomicas_para_letras(atomicas)
        formula = construir_formula_cpc(frase_norm, mapping)

        return jsonify({
            "ok": True,
            "frase_normalizada": frase_norm,
            "formula_cpc": formula,
            "mapeamento": mapping
        })

    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500


@app.route("/api/cpc-to-nl", methods=["POST"])
def api_cpc_to_nl():
    data = request.get_json(force=True)
    formula = data.get("formula", "").strip()
    mapping = data.get("mapeamento", {})

    if not formula:
        return jsonify({"ok": False, "erro": "Campo 'formula' obrigatório."}), 400

    if not mapping:
        return jsonify({"ok": False, "erro": "Campo 'mapeamento' obrigatório."}), 400

    try:
        expr = cpc_para_sympy(formula)
        frase_nl = expr_para_nl(expr, mapping)
        return jsonify({"ok": True, "frase_nl": frase_nl})

    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500


@app.route("/")
def raiz():
    return send_from_directory(".", "index.html")


# ---------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

