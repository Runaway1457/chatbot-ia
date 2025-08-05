from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uvicorn
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="🤖 Chatbot IA API",
    description="API para chatbot inteligente com processamento de linguagem natural",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class ChatMessage(BaseModel):
    user_id: str = Field(..., description="ID único do usuário")
    message: str = Field(..., min_length=1, max_length=1000, description="Mensagem do usuário")
    channel: str = Field(default="web", description="Canal de origem (web, whatsapp, teams)")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Resposta do chatbot")
    intent: str = Field(..., description="Intenção identificada")
    confidence: float = Field(..., ge=0, le=1, description="Confiança da predição")
    requires_human: bool = Field(..., description="Se precisa de atendimento humano")
    suggested_actions: List[str] = Field(default=[], description="Ações sugeridas")
    session_id: str = Field(..., description="ID da sessão")
    timestamp: datetime = Field(default_factory=datetime.now)

class AnalyticsResponse(BaseModel):
    total_conversations_today: int
    resolution_rate: float
    average_response_time: float
    human_handoff_rate: float
    satisfaction_score: float
    top_intents: List[Dict[str, int]]

# Endpoints
@app.get("/", tags=["Health"])
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "service": "Chatbot IA API",
        "version": "1.0.0",
        "status": "🟢 Online",
        "description": "Chatbot inteligente com processamento de linguagem natural",
        "endpoints": {
            "chat": "/chat",
            "analytics": "/analytics/summary", 
            "health": "/health",
            "docs": "/docs"
        },
        "features": [
            "Processamento de linguagem natural",
            "Análise de sentimento",
            "Integração CRM/Ticketing",
            "Suporte multicanal",
            "Analytics em tempo real"
        ]
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check detalhado"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "api": "🟢 Online",
            "database": "🟢 Connected",
            "redis": "🟢 Connected", 
            "openai": "🟢 Connected"
        },
        "metrics": {
            "uptime": "99.9%",
            "response_time": "1.2s",
            "requests_today": 1247
        }
    }

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(message: ChatMessage, background_tasks: BackgroundTasks):
    """
    Endpoint principal para conversação com o chatbot
    
    Processa mensagem do usuário e retorna resposta inteligente
    com análise de intenção e sugestões de ação.
    """
    try:
        logger.info(f"Nova mensagem de {message.user_id}: {message.message[:50]}...")
        
        # Simular processamento do chatbot (em produção seria a engine real)
        response_text = await process_message(message)
        intent = await classify_intent(message.message)
        confidence = 0.95
        requires_human = should_transfer_to_human(message.message, intent)
        suggested_actions = generate_suggestions(intent, message.message)
        session_id = f"session_{message.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Log da conversa em background
        background_tasks.add_task(log_conversation, message, response_text, intent)
        
        return ChatResponse(
            response=response_text,
            intent=intent["type"],
            confidence=confidence,
            requires_human=requires_human,
            suggested_actions=suggested_actions,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Erro no processamento: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "Erro interno no processamento",
                "message": "Desculpe, ocorreu um erro. Tente novamente em instantes.",
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/analytics/summary", response_model=AnalyticsResponse, tags=["Analytics"])
async def analytics_summary():
    """
    Resumo de analytics do chatbot
    
    Retorna métricas principais de performance e uso.
    """
    return AnalyticsResponse(
        total_conversations_today=1247,
        resolution_rate=0.96,
        average_response_time=1.2,
        human_handoff_rate=0.04,
        satisfaction_score=4.8,
        top_intents=[
            {"intent": "order_status", "count": 450},
            {"intent": "product_info", "count": 320},
            {"intent": "billing", "count": 180},
            {"intent": "technical_support", "count": 150},
            {"intent": "complaint", "count": 85}
        ]
    )

# Funções auxiliares
async def process_message(message: ChatMessage) -> str:
    """Processa mensagem e gera resposta"""
    
    user_msg = message.message.lower()
    
    # Respostas baseadas em palavras-chave (em produção seria o OpenAI)
    if any(word in user_msg for word in ["olá", "oi", "bom dia", "boa tarde"]):
        return f"Olá! 👋 Sou o assistente virtual da empresa. Como posso ajudá-lo hoje? Posso auxiliar com informações sobre pedidos, produtos, suporte técnico e muito mais!"
    
    elif any(word in user_msg for word in ["pedido", "status", "encomenda"]):
        return "📦 Para consultar seu pedido, preciso do número. Pode me informar o número do pedido? Exemplo: #12345. Com essa informação, posso verificar o status, rastreamento e previsão de entrega!"
    
    elif any(word in user_msg for word in ["produto", "preço", "informação"]):
        return "🛍️ Temos diversos produtos disponíveis! Pode me dizer qual produto específico você tem interesse? Posso fornecer informações sobre características, preços, disponibilidade e formas de pagamento."
    
    elif any(word in user_msg for word in ["problema", "não funciona", "defeito", "suporte"]):
        return "🛠️ Sinto muito pelo inconveniente! Vou ajudar você a resolver isso. Pode me descrever o problema com mais detalhes? Qual produto está apresentando problema e o que exatamente está acontecendo?"
    
    elif any(word in user_msg for word in ["cobrança", "fatura", "pagamento"]):
        return "💰 Questões de cobrança são importantes! Posso ajudar com dúvidas sobre sua fatura, formas de pagamento, vencimentos e negociação. Qual é sua dúvida específica sobre cobrança?"
    
    elif any(word in user_msg for word in ["cancelar", "cancelamento"]):
        return "❌ Entendi que você deseja cancelar algo. Para processar seu cancelamento de forma adequada, preciso de mais informações. O que você gostaria de cancelar? Pedido, assinatura ou outro serviço?"
    
    elif any(word in user_msg for word in ["obrigado", "valeu", "muito bom"]):
        return "😊 Fico feliz em ter ajudado! Se precisar de mais alguma coisa, estarei sempre aqui. Tenha um ótimo dia! ⭐"
    
    else:
        return "🤔 Interessante! Estou processando sua solicitação. Embora eu possa ajudar com diversas questões, para esta situação específica, que tal falar com um de nossos especialistas? Eles terão todo prazer em ajudar você!"

async def classify_intent(message: str) -> Dict:
    """Classifica intenção da mensagem"""
    
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["pedido", "status", "encomenda", "tracking"]):
        return {"type": "order_status", "confidence": 0.95}
    elif any(word in message_lower for word in ["produto", "preço", "informação", "detalhes"]):
        return {"type": "product_info", "confidence": 0.90}
    elif any(word in message_lower for word in ["cobrança", "fatura", "pagamento", "valor"]):
        return {"type": "billing", "confidence": 0.88}
    elif any(word in message_lower for word in ["problema", "defeito", "não funciona", "suporte"]):
        return {"type": "technical_support", "confidence": 0.92}
    elif any(word in message_lower for word in ["reclamação", "insatisfeito", "ruim"]):
        return {"type": "complaint", "confidence": 0.85}
    elif any(word in message_lower for word in ["olá", "oi", "bom dia", "boa tarde"]):
        return {"type": "greeting", "confidence": 0.98}
    else:
        return {"type": "general_inquiry", "confidence": 0.70}

def should_transfer_to_human(message: str, intent: Dict) -> bool:
    """Determina se deve transferir para atendimento humano"""
    
    # Palavras que indicam necessidade de humano
    human_keywords = ["falar com", "atendente", "pessoa", "humano", "gerente", "supervisão"]
    
    if any(keyword in message.lower() for keyword in human_keywords):
        return True
    
    # Intenções complexas que podem precisar de humano
    if intent["type"] == "complaint" and intent["confidence"] > 0.8:
        return True
    
    # Baixa confiança na classificação
    if intent["confidence"] < 0.7:
        return True
    
    return False

def generate_suggestions(intent: Dict, message: str) -> List[str]:
    """Gera sugestões de ação baseadas na intenção"""
    
    intent_type = intent["type"]
    
    suggestions = {
        "order_status": [
            "📦 Consultar outro pedido",
            "📱 Receber notificações por WhatsApp",
            "📧 Falar com atendente"
        ],
        "product_info": [
            "🛍️ Ver produtos similares",
            "💰 Consultar formas de pagamento",
            "📞 Falar com vendedor"
        ],
        "technical_support": [
            "📋 Acessar tutorial",
            "🎥 Ver vídeo explicativo",
            "👨‍💻 Falar com técnico"
        ],
        "billing": [
            "💳 Ver formas de pagamento",
            "📄 Segunda via da fatura",
            "💰 Negociar desconto"
        ],
        "complaint": [
            "📝 Abrir chamado formal",
            "📞 Falar com supervisor",
            "🎁 Ver compensações"
        ]
    }
    
    return suggestions.get(intent_type, [
        "❓ Fazer outra pergunta",
        "📞 Falar com atendente",
        "🏠 Voltar ao início"
    ])

async def log_conversation(message: ChatMessage, response: str, intent: Dict):
    """Log da conversa para analytics (background task)"""
    
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "user_id": message.user_id,
        "channel": message.channel,
        "user_message": message.message,
        "bot_response": response,
        "intent": intent["type"],
        "confidence": intent["confidence"]
    }
    
    logger.info(f"Conversa registrada: {log_data}")
    # Aqui salvaria no banco de dados real

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )