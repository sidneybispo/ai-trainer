from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor
from langchain.agents.agent_types import AgentType
from langchain.callbacks import get_openai_callback
from database import listar_tabelas, obter_schema

def criar_agente(engine):
    db = SQLDatabase(engine)
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3
    )
    
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    )

    return agent_executor

def fazer_pergunta(agente, engine, pergunta):
    tabelas = listar_tabelas(engine)
    schemas = {table: obter_schema(engine, table) for table in tabelas}
    
    contexto = "Você é um Cientista de Dados Expert em IA. "
    contexto += f"As tabelas disponíveis são: {', '.join(tabelas)}. "
    for table, schema in schemas.items():
        colunas = [f"{col['name']} ({col['type']})" for col in schema]
        contexto += f"A tabela {table} tem as seguintes colunas: {', '.join(colunas)}. "
    
    contexto += ("Use essas informações para responder à pergunta do usuário. "
                 "Se for necessário realizar uma consulta SQL para responder, "
                 "faça-o e inclua o SQL usado na sua resposta.")
    
    pergunta_completa = f"{contexto}\n\nPergunta do usuário: {pergunta}"

    with get_openai_callback() as cb:
        resposta = agente.run(pergunta_completa)

    # Extrair o SQL da resposta, se presente
    sql_usado = extrair_sql_da_resposta(resposta)

    return resposta, sql_usado

def extrair_sql_da_resposta(resposta):
    import re
    sql_match = re.search(r'```sql\n(.*?)\n```', resposta, re.DOTALL)
    if sql_match:
        return sql_match.group(1)
    return ""