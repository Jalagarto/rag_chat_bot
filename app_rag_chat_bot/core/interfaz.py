import gradio as gr

def create_interface(app) -> gr.Blocks:
    with gr.Blocks(title="RAG Chatbot con Memoria Dinámica") as demo:
        with gr.Row():
            gr.Markdown("# RAG Chatbot con Memoria Dinámica")
        
        with gr.Row():
            gr.Markdown("""
            Este chatbot utiliza RAG (Retrieval-Augmented Generation) para responder preguntas basadas en documentos PDF.
            También cuenta con memoria dinámica que resume automáticamente conversaciones largas y capacidad de ejecutar código Python
            para respuestas que requieren precisión numérica.
            """)
        
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("### Gestión de Documentos")
                    file_upload = gr.File(
                        file_types=[".pdf"], 
                        file_count="multiple",
                        label="Cargar documentos PDF"
                    )
                    upload_button = gr.Button("Procesar documentos", variant="primary")
                    upload_status = gr.Textbox(label="Estado de carga", interactive=False)
                
                with gr.Accordion("Configuración", open=False):
                    gr.Markdown("### Parámetros del Chatbot")
                    temperature_slider = gr.Slider(
                        minimum=0.0, maximum=1.0, value=0.2, step=0.1,
                        label="Temperature (creatividad)"
                    )
            
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(height=400, label="Conversación")
                
                with gr.Row():
                    with gr.Column(scale=8):
                        user_input = gr.Textbox(
                            placeholder="Escribe tu pregunta aquí...",
                            label="Pregunta",
                            lines=2
                        )
                    with gr.Column(scale=1):
                        submit_button = gr.Button("Enviar", variant="primary")
                
                with gr.Row():
                    clear_button = gr.Button("Limpiar conversación")
                    regenerate_button = gr.Button("Regenerar respuesta")
        
        # Definir eventos utilizando los métodos de la clase ChatbotApp
        upload_button.click(
            fn=app._process_files,
            inputs=[file_upload],
            outputs=[upload_status]
        )
        
        submit_button.click(
            fn=app._chat_and_log,
            inputs=[user_input, chatbot],
            outputs=[user_input, chatbot]
        )
        
        user_input.submit(
            fn=app._chat_and_log,
            inputs=[user_input, chatbot],
            outputs=[user_input, chatbot]
        )
        
        clear_button.click(
            fn=app._clear_chat,
            inputs=None,
            outputs=[chatbot]
        )
        
        regenerate_button.click(
            fn=app._regenerate_response,
            inputs=[chatbot],
            outputs=[chatbot]
        )
    
    return demo