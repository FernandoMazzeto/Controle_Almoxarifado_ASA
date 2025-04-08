from fastapi import APIRouter, Depends, HTTPException, Response, status
from schemas.pedidos import Pedido as PedidoSchema
from models.pedidos import Pedido
from sqlalchemy.orm import Session
from models.database import get_db
import pika
import json

router = APIRouter()


@router.get("/pedidos")
async def root():
    return {"mensagem": "Dentro de pedidos"}


@router.post("/pedidos")
def cria_pedidos(pedido: PedidoSchema, db: Session = Depends(get_db)):
    try:
        novo_pedido = Pedido(**pedido.model_dump())
        db.add(novo_pedido)
        db.commit()
        db.refresh(novo_pedido)
        return novo_pedido
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Problemas ao inserir o pedido"
        )


@router.post("/pedidos/{id}")
def pesquisa_pedido(id: int, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id == id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail=f"Pedido {id} não existe")
    return pedido


@router.put("/pedidos/{id}")
def update(id: int, pedido: PedidoSchema, db: Session = Depends(get_db)):
    pedido_db = db.query(Pedido).filter(Pedido.id == id)
    if not pedido_db.first():
        raise HTTPException(status_code=404, detail=f"Pedido {id} não existe")
    pedido_db.update(pedido.model_dump(), synchronize_session=False)
    db.commit()
    return pedido_db.first()


@router.delete("/pedidos/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id == id)
    if not pedido.first():
        raise HTTPException(status_code=404, detail="Pedido não existe")
    pedido.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/enviar-pedido/{id}")
def enviar_pedido_fila(id: int, db: Session = Depends(get_db)):
    try:
        pedido = db.query(Pedido).filter(Pedido.id == id).first()

        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")

        pedido_dict = {
            "id": pedido.id,
            "produto": pedido.produto,
            "quantidade": pedido.quantidade,
            "status": "enviado_almoxarifado"
        }

        # Conecta ao RabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rabbitmq', port=5672)
        )
        channel = connection.channel()
        
        channel.queue_declare(queue='fila_pedidos')

        channel.basic_publish(
            exchange='',
            routing_key='fila_pedidos',
            body=json.dumps(pedido_dict)
        )

        connection.close()
        return {"mensagem": f"Pedido {id} enviado ao almoxarifado"}

    except Exception as e:
        print(f"Erro ao publicar no RabbitMQ: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao publicar no RabbitMQ: {str(e)}")

@router.post("/processar-pedido/{id}")
def processar_pedido_por_id(id: int, db: Session = Depends(get_db)):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', port=5672))
        channel = connection.channel()
        channel.queue_declare(queue='fila_pedidos')

        while True:
            method_frame, header_frame, body = channel.basic_get(queue='fila_pedidos')

            if not method_frame:
                connection.close()
                return {"mensagem": f"Nenhum pedido com id {id} encontrado na fila"}

            pedido_data = json.loads(body.decode('utf-8'))

            if pedido_data['id'] == id:
                pedido = db.query(Pedido).filter(Pedido.id == id).first()
                if pedido:
                    pedido.status = "processado_almoxarifado"
                    db.commit()
                    db.refresh(pedido)

                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                connection.close()
                return {"mensagem": f"Pedido {id} processado com sucesso", "pedido": pedido_data}
            else:
                channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)
                break  

        connection.close()
        return {"mensagem": f"Pedido {id} não encontrado na fila nesta tentativa"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar pedido: {str(e)}")
