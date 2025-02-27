import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import os
import json
import time
from datetime import datetime
import uuid
import functools

class TimeTrackerApp(toga.App):
    def startup(self):
        """Inicia o aplicativo garantindo que os tempos sejam resetados."""
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.log_folder = os.path.join(self.paths.data, "logs")
        os.makedirs(self.log_folder, exist_ok=True)
        self.settings_file = os.path.join(self.log_folder, "settings.json")
        self.log_file = os.path.join(self.log_folder, "tracking_logs.json")

        # 🔹 Resetar todos os tempos na inicialização
        self.current_stage = None
        self.start_time = None

        # 🔹 Criar um arquivo de logs vazio se ele não existir
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                json.dump([], f, indent=4)

        # 🔹 Resetar tempos e horários das etapas
        self.load_stages()
        for stage in self.stages.values():
            stage["tempos"] = []
            stage["hora_inicio"] = None
            stage["hora_fim"] = None
            stage["horarios"] = []

        self.main_content_top = self.create_static_layout_top()
        self.dynamic_content = self.create_dynamic_buttons()
        self.main_content_bot = self.create_static_layout_bot()

        self.main_window.content = toga.Box(
            children=[self.main_content_top, self.dynamic_content, self.main_content_bot],
            style=Pack(direction=COLUMN)
        )

        self.main_window.toolbar.add(
            toga.Command(self.open_settings, text="Configurações", group=toga.Group.APP)
        )

        self.main_window.show()


    def load_stages(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r") as f:
                self.stages = json.load(f)
        else:
            self.stages = {
                f"Etapa {i+1}": {"nome": f"Etapa {i+1}", "codigo": f"{i+1:04}", "tempos": []}
                for i in range(8)
            }
            with open(self.settings_file, "w") as f:
                json.dump(self.stages, f)

    def create_static_layout_top(self):
        jira_label = toga.Label("Card JIRA:", style=Pack(padding=5))
        self.jira_input = toga.TextInput(placeholder="Digite o card JIRA", style=Pack(flex=1, padding=5))
        jira_box = toga.Box(children=[jira_label, self.jira_input], style=Pack(direction=ROW, padding=10))
        return toga.Box(
            children=[jira_box],
            style=Pack(direction=COLUMN, padding=10)
        )
    
    def create_static_layout_bot(self):
        self.time_label = toga.Label("Tempo total: 0 segundos", style=Pack(padding=10))
        finish_button = toga.Button("Finalizar", on_press=self.finish_tracking, style=Pack(padding=10))
        logs_button = toga.Button("Consultar Logs", on_press=self.view_logs, style=Pack(padding=10))
        return toga.Box(
            children=[self.time_label, finish_button, logs_button],
            style=Pack(direction=COLUMN, padding=10)
        )

    def create_dynamic_buttons(self):
        button_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.buttons = {}
        for i, (stage_name, stage_data) in enumerate(self.stages.items()):
            button = toga.Button(
                stage_data["nome"],
                on_press=self.handle_stage,
                id=stage_name,
                style=Pack(flex=1, padding=5)
            )
            self.buttons[stage_name] = button
            if i % 2 == 0:
                row = toga.Box(style=Pack(direction=ROW, padding=5))
                button_box.add(row)
            row.add(button)
        return button_box


    def open_settings(self, widget):
        """Abre a janela de configurações com opção de zerar logs."""
        settings_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        self.settings_inputs = {}
        for stage, data in self.stages.items():
            row = toga.Box(style=Pack(direction=ROW, padding=5))
            name_input = toga.TextInput(value=data['nome'], style=Pack(flex=1, padding=5))
            code_input = toga.TextInput(value=data['codigo'], style=Pack(flex=1, padding=5))
            self.settings_inputs[stage] = {'nome': name_input, 'codigo': code_input}
            row.add(toga.Label(stage, style=Pack(padding=5)))
            row.add(name_input)
            row.add(code_input)
            settings_box.add(row)

        save_button = toga.Button("Salvar", on_press=self.save_settings, style=Pack(padding=10))
        reset_logs_button = toga.Button("Zerar Logs", on_press=self.clear_logs, style=Pack(padding=10, background_color="#f44336", color="white"))
        back_button = toga.Button("Voltar", on_press=self.return_to_main, style=Pack(padding=10))

        settings_box.add(save_button)
        settings_box.add(reset_logs_button)
        settings_box.add(back_button)

        self.main_window.content = settings_box


    def save_settings(self, widget):
        for stage, inputs in self.settings_inputs.items():
            self.stages[stage]['nome'] = inputs['nome'].value
            self.stages[stage]['codigo'] = inputs['codigo'].value
        with open(self.settings_file, "w") as f:
            json.dump(self.stages, f, indent=4)
        self.return_to_main(widget)

    def return_to_main(self, widget):
        self.dynamic_content = self.create_dynamic_buttons()
        self.main_window.content = toga.Box(
            children=[self.main_content_top, self.dynamic_content,self.main_content_bot],
            style=Pack(direction=COLUMN)
        )

    def view_logs(self, widget):
        """Exibe a interface de consulta de logs, verificando se o JSON é válido."""
        if not os.path.exists(self.log_file):
            self.main_window.info_dialog("Logs", "Nenhum log encontrado.")
            return

        try:
            with open(self.log_file, "r") as f:
                self.logs = json.load(f)

            # Se o JSON estiver vazio ou incorreto, inicializa como uma lista vazia
            if not isinstance(self.logs, list):
                self.logs = []
        except (json.JSONDecodeError, ValueError):
            # Se houver erro, recria o arquivo JSON vazio
            with open(self.log_file, "w") as f:
                json.dump([], f, indent=4)

            self.logs = []
            self.main_window.info_dialog("Erro nos Logs", "O arquivo de logs estava corrompido e foi resetado.")

        # Se não houver logs após reset, avisa o usuário
        if not self.logs:
            self.main_window.info_dialog("Logs", "Nenhum log encontrado.")
            return

        self.logs_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        self.search_input = toga.TextInput(
            placeholder="Buscar por data, token ou card JIRA",
            style=Pack(flex=1, padding=5)
        )
        search_button = toga.Button(
            "Buscar",
            on_press=self.search_logs,
            style=Pack(padding=5)
        )
        back_button = toga.Button(
            "Voltar",
            on_press=self.return_to_main,
            style=Pack(padding=10)
        )

        self.logs_box.add(self.search_input)
        self.logs_box.add(search_button)
        self.logs_box.add(back_button)

        self.results_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.logs_box.add(self.results_box)

        self.details_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.logs_box.add(self.details_box)

        self.main_window.content = self.logs_box

    def search_logs(self, widget):
        """Filtra os logs de acordo com a busca e exibe os resultados."""
        query = self.search_input.value.strip()
        if not query:
            return

        filtered_logs = [
            log for log in self.logs
            if query in log["data_finalizacao"] or query in log["token"] or query in log["card_jira"]
        ]

        # Limpa os resultados e os detalhes anteriores
        for child in self.results_box.children[:]:
            self.results_box.remove(child)
        for child in self.details_box.children[:]:
            self.details_box.remove(child)

        if not filtered_logs:
            # Se nenhum resultado for encontrado, exibir mensagem
            no_results_label = toga.Label(
                "Nenhum resultado encontrado.",
                style=Pack(padding=10, font_weight="bold", color="red")
            )
            self.results_box.add(no_results_label)
            return  # Sai da função para não tentar exibir logs inexistentes

        for log in filtered_logs:
            log_box = toga.Box(style=Pack(direction=COLUMN, padding=8, background_color="#f5f5f5"))

            log_button = toga.Button(
                f"Data: {log['data_finalizacao']} | Card: {log['card_jira']}",
                on_press=functools.partial(self.display_log_details, log),
                style=Pack(padding=5, font_weight="bold", color="blue", text_align="left")
            )

            log_box.add(log_button)
            log_box.add(toga.Label("Clique para mais detalhes", style=Pack(padding=2, font_size=10, color="gray")))

            self.results_box.add(log_box)
    
    def update_time(self, inicio_input, fim_input, tempo_label):
        """Recalcula automaticamente o tempo baseado no início e fim."""
        inicio = inicio_input.value.strip()
        fim = fim_input.value.strip()

        # Se algum valor estiver vazio, definir como 00:00:00
        if not inicio:
            inicio = "00:00:00"
        if not fim:
            fim = "00:00:00"

        try:
            t_inicio = datetime.strptime(inicio, "%H:%M:%S")
            t_fim = datetime.strptime(fim, "%H:%M:%S")

            # Calcular tempo total em segundos
            tempo_total = int((t_fim - t_inicio).total_seconds())
            if tempo_total < 0:
                tempo_total = 0  # Evita valores negativos

            tempo_label.text = str(tempo_total)  # Atualiza a interface
        except ValueError:
            tempo_label.text = "0"  # Se der erro no formato, colocar como 0


    def display_log_details(self, log, widget=None):
        """Mostra um resumo do log (etapa, código, tempo total) e permite entrar no modo de edição."""
        self.current_token = log["token"]  # Salva o token do log atual

        # 🔹 Limpa a área antes de exibir novos dados
        for child in self.details_box.children[:]:
            self.details_box.remove(child)

        # 🔹 Exibir cabeçalho
        header = toga.Box(style=Pack(direction=ROW, padding=5, background_color='#dcdcdc'))
        header.add(toga.Label("Etapa", style=Pack(width=100, padding=5, font_weight="bold")))
        header.add(toga.Label("Código", style=Pack(width=80, padding=5, font_weight="bold")))
        header.add(toga.Label("Tempo (segundos)", style=Pack(width=80, padding=5, font_weight="bold")))
        self.details_box.add(header)

        # 🔹 Criar um dicionário para agrupar os tempos por etapa
        etapas_resumidas = {}
        for etapa in log["etapas"]:
            chave = (etapa["etapa"], etapa["codigo"])
            if chave not in etapas_resumidas:
                etapas_resumidas[chave] = 0
            etapas_resumidas[chave] += etapa["tempo"]

        # 🔹 Exibir apenas o resumo na tela
        for (etapa, codigo), tempo_total in etapas_resumidas.items():
            row = toga.Box(style=Pack(direction=ROW, padding=5))
            row.add(toga.Label(etapa, style=Pack(width=100, padding=5)))
            row.add(toga.Label(codigo, style=Pack(width=80, padding=5)))
            row.add(toga.Label(str(round(tempo_total, 2)), style=Pack(width=80, padding=5)))
            self.details_box.add(row)

        # 🔹 Botão "Editar" para mostrar os detalhes completos
        edit_button = toga.Button(
            "Editar",
            on_press=lambda x: self.show_detailed_edit_view(log),
            style=Pack(padding=10, background_color="#FFC107", color="black")
        )
        self.details_box.add(edit_button)

    def show_detailed_edit_view(self, log):
        """Mostra todas as ocorrências individuais para edição em ordem cronológica."""
        # 🔹 Limpa os detalhes antes de exibir os editáveis
        for child in self.details_box.children[:]:
            self.details_box.remove(child)

        # 🔹 Ordenar os logs pelo horário de início antes de exibir
        log["etapas"].sort(key=lambda x: datetime.strptime(x["inicio"], "%H:%M:%S"))

        # 🔹 Cabeçalho da edição com largura flexível
        header = toga.Box(style=Pack(direction=ROW, padding=5, background_color='#dcdcdc'))
        header.add(toga.Label("Etapa", style=Pack(flex=1, padding=5, font_weight="bold")))
        header.add(toga.Label("Código", style=Pack(flex=1, padding=5, font_weight="bold")))
        header.add(toga.Label("Início", style=Pack(flex=2, padding=5, font_weight="bold")))  # Mais espaço para inputs
        header.add(toga.Label("Fim", style=Pack(flex=2, padding=5, font_weight="bold")))  # Mais espaço para inputs
        header.add(toga.Label("Tempo (seg)", style=Pack(flex=1, padding=5, font_weight="bold")))
        self.details_box.add(header)

        # 🔹 Criar campos editáveis para cada entrada individual
        self.edit_inputs = []
        for etapa in log["etapas"]:
            row = toga.Box(style=Pack(direction=ROW, padding=5))

            etapa_label = toga.Label(etapa["etapa"], style=Pack(flex=1, padding=5))
            codigo_label = toga.Label(etapa["codigo"], style=Pack(flex=1, padding=5))
            inicio_input = toga.TextInput(value=etapa["inicio"], style=Pack(flex=2, padding=5))
            fim_input = toga.TextInput(value=etapa["fim"], style=Pack(flex=2, padding=5))
            tempo_label = toga.Label(str(round(etapa["tempo"], 2)), style=Pack(flex=1, padding=5))

            # Guardar inputs para edição
            self.edit_inputs.append({
                "etapa": etapa_label,
                "codigo": codigo_label,
                "inicio": inicio_input,
                "fim": fim_input,
                "tempo_label": tempo_label
            })

            row.add(etapa_label)
            row.add(codigo_label)
            row.add(inicio_input)
            row.add(fim_input)
            row.add(tempo_label)
            self.details_box.add(row)

            # Atualizar tempo automaticamente ao alterar os valores de início e fim
            inicio_input.on_change = lambda widget: self.update_time(inicio_input, fim_input, tempo_label)
            fim_input.on_change = lambda widget: self.update_time(inicio_input, fim_input, tempo_label)

        # 🔹 Botão "Salvar Alterações"
        save_button = toga.Button(
            "Salvar Alterações",
            on_press=lambda x: self.save_edited_log(),
            style=Pack(padding=10, background_color="#4CAF50", color="white", flex=1)
        )
        self.details_box.add(save_button)

    def save_edited_log(self):
        """Salva as edições feitas nos detalhes do log e remove linhas vazias."""
        with open(self.log_file, "r") as f:
            logs = json.load(f)
        # Encontrar o log correto pelo token
        for log in logs:
            if log["token"] == self.current_token:
                novas_etapas = []

                for i, etapa in enumerate(log["etapas"]):
                    if i < len(self.edit_inputs):  # Evita erro de índice
                        inicio = self.edit_inputs[i]["inicio"].value.strip() or "00:00:00"
                        fim = self.edit_inputs[i]["fim"].value.strip() or "00:00:00"

                        try:
                            t_inicio = datetime.strptime(inicio, "%H:%M:%S")
                            t_fim = datetime.strptime(fim, "%H:%M:%S")
                            tempo_total = int((t_fim - t_inicio).total_seconds())
                            if tempo_total < 0:
                                tempo_total = 0
                        except ValueError:
                            tempo_total = 0  # Se houver erro no formato, define como 0

                        # Se os valores forem válidos, adiciona ao JSON
                        if inicio != "00:00:00" or fim != "00:00:00":
                            novas_etapas.append({
                                "etapa": etapa["etapa"],
                                "codigo": etapa["codigo"],
                                "inicio": inicio,
                                "fim": fim,
                                "tempo": tempo_total
                            })

                # Atualiza o log com as novas etapas (removendo as que foram apagadas)
                log["etapas"] = novas_etapas

        # Salvar os logs editados no JSON
        with open(self.log_file, "w") as f:
            json.dump(logs, f, indent=4)

        self.main_window.info_dialog("Sucesso", "Log atualizado com sucesso!")


    async def clear_logs(self, widget):
        """Solicita confirmação antes de apagar todos os logs."""
        dialog = toga.ConfirmDialog(
            title="Confirmação",
            message="Tem certeza que deseja apagar todos os logs? Essa ação não pode ser desfeita.",
        )
        confirm = await self.main_window.dialog(dialog)  # Aguarda resposta

        if confirm:
            # Apaga o conteúdo do arquivo de logs
            if os.path.exists(self.log_file):
                with open(self.log_file, "w") as f:
                    json.dump([], f, indent=4)

            # Verifica se results_box e details_box existem antes de tentar limpá-los
            if hasattr(self, "results_box") and self.results_box:
                for child in self.results_box.children[:]:
                    self.results_box.remove(child)
            if hasattr(self, "details_box") and self.details_box:
                for child in self.details_box.children[:]:
                    self.details_box.remove(child)

            # Exibe confirmação de que os logs foram apagados
            info_dialog = toga.InfoDialog(
                title="Sucesso",
                message="Todos os logs foram apagados com sucesso."
            )
            await self.main_window.dialog(info_dialog)
    
    def handle_stage(self, widget):
        """Gerencia a seleção de etapas e o tempo registrado."""
        now = time.time()
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Se já havia uma etapa ativa, salva o tempo e o horário de fim
        if self.current_stage:
            elapsed = now - self.start_time
            self.stages[self.current_stage]["tempos"].append(elapsed)

            if "horarios" not in self.stages[self.current_stage]:
                self.stages[self.current_stage]["horarios"] = []

            self.stages[self.current_stage]["horarios"].append({
                "inicio": self.stages[self.current_stage]["hora_inicio"],
                "fim": timestamp,
                "tempo": elapsed
            })

            self.stages[self.current_stage]["hora_fim"] = timestamp
            del self.buttons[self.current_stage].style.background_color

        # Atualiza a nova etapa e registra um novo horário de início
        self.current_stage = widget.id
        self.start_time = now

        if "horarios" not in self.stages[self.current_stage]:
            self.stages[self.current_stage]["horarios"] = []

        self.stages[self.current_stage]["hora_inicio"] = timestamp  # Registra o início da nova etapa
        widget.style.background_color = "lightblue"


    def finish_tracking(self, widget):
        """Finaliza a contagem de tempo e exibe o resumo (simplificado), mas salva o log completo."""
        if self.current_stage:
            elapsed = time.time() - self.start_time
            self.stages[self.current_stage]["tempos"].append(elapsed)

            if "horarios" not in self.stages[self.current_stage]:
                self.stages[self.current_stage]["horarios"] = []

            self.stages[self.current_stage]["horarios"].append({
                "inicio": self.stages[self.current_stage]["hora_inicio"],
                "fim": datetime.now().strftime("%H:%M:%S"),
                "tempo": elapsed
            })

            self.stages[self.current_stage]["hora_fim"] = datetime.now().strftime("%H:%M:%S")

        jira_card = self.jira_input.value.strip() or "SEM CARD JIRA"
        total_time = sum(sum(stage["tempos"]) for stage in self.stages.values())

        # 🔹 Criar log completo com todas as ocorrências separadas
        log_completo = []
        for stage_name, data in self.stages.items():
            if "horarios" in data and len(data["horarios"]) > 0:
                for horario in data["horarios"]:
                    log_completo.append({
                        "etapa": data["nome"],
                        "codigo": data["codigo"],
                        "inicio": horario["inicio"],
                        "fim": horario["fim"],
                        "tempo": horario["tempo"]
                    })

        # 🔹 Criar log resumido apenas com etapas agrupadas e tempos somados
        etapas_agrupadas = {}
        for item in log_completo:
            chave = (item["etapa"], item["codigo"])
            if chave not in etapas_agrupadas:
                etapas_agrupadas[chave] = 0
            etapas_agrupadas[chave] += item["tempo"]

        # 🔹 Exibir apenas o resumo na tela
        resumo_text = f"Card JIRA: {jira_card}\nToken: {uuid.uuid4().hex}\n\n"
        for (etapa, codigo), tempo in etapas_agrupadas.items():
            resumo_text += f"Etapa: {etapa}\nCódigo: {codigo}\nTempo: {self.format_time(tempo)}\n\n"

        resumo_text += f"Tempo Total: {self.format_time(total_time)}"
        self.main_window.info_dialog("Resumo do Acompanhamento", resumo_text)

        # 🔹 Agora salvamos o log completo!
        self.save_log(uuid.uuid4().hex, jira_card, log_completo)

        # 🔹 Resetar estados para um novo acompanhamento
        for stage in self.stages.values():
            stage["tempos"] = []
            stage["hora_inicio"] = None
            stage["hora_fim"] = None
            stage["horarios"] = []

        self.current_stage = None
        self.start_time = None
        self.jira_input.value = ""
        self.time_label.text = "Tempo total: 0 segundos"

        # Resetar botões (remover cores de seleção)
        for button in self.buttons.values():
            del button.style.background_color


    def format_time(self, seconds):
        if seconds < 60:
            return f"{int(seconds)} segundos"
        minutes = seconds // 60
        return f"{int(minutes)} minutos"

    def save_log(self, token, jira_card, log_completo):
        """Salva os logs garantindo que o JSON seja válido."""
        log_data = {
            "token": token,
            "data_finalizacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "card_jira": jira_card,
            "etapas": log_completo  # 🔹 Salva o log completo
        }

        # 🔹 Verifica se o arquivo de logs existe e contém um JSON válido
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    logs = json.load(f)
                    if not isinstance(logs, list):
                        logs = []  # Se não for uma lista, recria
            except (json.JSONDecodeError, ValueError):
                logs = []  # Se o JSON estiver corrompido, recria a lista vazia
        else:
            logs = []

        logs.append(log_data)  # Adiciona o novo log

        # 🔹 Salva os logs garantindo um JSON formatado corretamente
        with open(self.log_file, "w") as f:
            json.dump(logs, f, indent=4)

        print("✅ Logs salvos com sucesso.")


def main():
    return TimeTrackerApp("Time Tracker", "com.viniciustorres.timetracker")