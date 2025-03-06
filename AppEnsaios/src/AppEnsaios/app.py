import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import os
import json
import time
from datetime import datetime
import uuid
import functools
import math

class TimeTrackerApp(toga.App):
    def startup(self):
        """Inicia o aplicativo garantindo que os tempos sejam resetados."""
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.log_folder = os.path.join(self.paths.data, "logs")
        os.makedirs(self.log_folder, exist_ok=True)
        self.settings_file = os.path.join(self.log_folder, "settings.json")
        self.log_file = os.path.join(self.log_folder, "tracking_logs.json")

        # Resetar todos os tempos na inicialização
        self.current_stage = None
        self.start_time = None

        # Criar um arquivo de logs vazio se ele não existir
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                json.dump([], f, indent=4)

        # Resetar tempos e horários das etapas
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
        """Carrega as etapas e o número de botões da configuração."""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
                self.num_buttons = settings.get("num_buttons", 8)  # 🔹 Valor padrão: 8 botões
                self.stages = settings.get("stages", {})
        else:
            self.num_buttons = 8  # 🔹 Valor padrão inicial
            self.stages = {
                f"Etapa {i+1}": {"nome": f"Etapa {i+1}", "codigo": f"{i+1:04}", "tempos": []}
                for i in range(self.num_buttons)
            }
            self.save_settings()


    def create_static_layout_top(self):
        jira_label = toga.Label("Card JIRA:", style=Pack(padding=5))
        self.jira_input = toga.TextInput(placeholder="Digite o card JIRA", style=Pack(flex=1, padding=5))
        jira_box = toga.Box(children=[jira_label, self.jira_input], style=Pack(direction=ROW, padding=10))
        return toga.Box(
            children=[jira_box],
            style=Pack(direction=COLUMN, padding=10)
        )
    
    def create_static_layout_bot(self):
        """Cria o layout inferior da interface"""
        self.finish_button = toga.Button("Finalizar", on_press=self.finish_tracking, style=Pack(padding=10))
        self.logs_button = toga.Button("Consultar Logs", on_press=self.view_logs, style=Pack(padding=10))

        return toga.Box(
            children=[self.finish_button, self.logs_button],
            style=Pack(direction=COLUMN, padding=10)
        )

    def create_dynamic_buttons(self):
        """Cria dinamicamente os botões de etapa conforme o número configurado."""
        button_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.buttons = {}

        for i in range(self.num_buttons):  # 🔹 Usa o número de botões configurado
            stage_name = f"Etapa {i+1}"
            if stage_name not in self.stages:
                self.stages[stage_name] = {"nome": stage_name, "codigo": f"{i+1:04}", "tempos": []}

            button = toga.Button(
                self.stages[stage_name]["nome"],
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
    
    def update_button_list(self):
        """Atualiza a lista de etapas conforme o número de botões escolhido."""
        new_stages = {}

        for i in range(self.num_buttons):
            stage_name = f"Etapa {i+1}"
            if stage_name in self.stages:
                new_stages[stage_name] = self.stages[stage_name]  # Mantém configurações antigas
            else:
                new_stages[stage_name] = {"nome": stage_name, "codigo": f"{i+1:04}", "tempos": []}  # Cria novas etapas

        self.stages = new_stages  # Atualiza o dicionário de etapas


    def open_settings(self, widget):
        """Abre a janela de configurações com opção de alterar o número de botões e zerar logs."""
        scroll_content = toga.Box(style=Pack(direction=COLUMN, padding=10))  # 🔹 Criamos um box rolável

        # 🔹 Seção para escolher o número de botões
        button_count_box = toga.Box(style=Pack(direction=ROW, padding=10))
        button_count_label = toga.Label(f"Quantidade de botões: {self.num_buttons}", style=Pack(padding=5))

        def decrease_buttons(widget):
            if self.num_buttons > 1:
                self.num_buttons -= 1
                button_count_label.text = f"Quantidade de botões: {self.num_buttons}"

        def increase_buttons(widget):
            if self.num_buttons < 20:
                self.num_buttons += 1
                button_count_label.text = f"Quantidade de botões: {self.num_buttons}"

        def generate_buttons(widget):
            """Atualiza a lista de botões dinamicamente na tela de configurações."""
            self.update_button_list()
            self.open_settings(widget)  # 🔹 Reabre a tela de configurações com os novos valores

        minus_button = toga.Button("-", on_press=decrease_buttons, style=Pack(padding=5))
        plus_button = toga.Button("+", on_press=increase_buttons, style=Pack(padding=5))
        generate_button = toga.Button("Gerar", on_press=generate_buttons, style=Pack(padding=5))

        button_count_box.add(minus_button)
        button_count_box.add(button_count_label)
        button_count_box.add(plus_button)
        button_count_box.add(generate_button)
        
        scroll_content.add(button_count_box)

        # 🔹 Criar uma caixa rolável para os botões configuráveis
        self.settings_inputs = {}

        for i in range(self.num_buttons):
            stage_name = f"Etapa {i+1}"
            if stage_name not in self.stages:
                self.stages[stage_name] = {"nome": stage_name, "codigo": f"{i+1:04}", "tempos": []}

            row = toga.Box(style=Pack(direction=ROW, padding=5))

            name_input = toga.TextInput(value=self.stages[stage_name]["nome"], style=Pack(flex=1, padding=5))
            code_input = toga.TextInput(value=self.stages[stage_name]["codigo"], style=Pack(flex=1, padding=5))

            self.settings_inputs[stage_name] = {'nome': name_input, 'codigo': code_input}

            row.add(toga.Label(stage_name, style=Pack(padding=5)))
            row.add(name_input)
            row.add(code_input)
            scroll_content.add(row)

        # 🔹 Botões para salvar ou voltar
        save_button = toga.Button("Salvar", on_press=self.save_settings, style=Pack(padding=10))
        reset_logs_button = toga.Button("Zerar Logs", on_press=self.clear_logs, style=Pack(padding=10, background_color="#f44336", color="white"))
        back_button = toga.Button("Voltar", on_press=self.return_to_main, style=Pack(padding=10))

        scroll_content.add(save_button)
        scroll_content.add(reset_logs_button)
        scroll_content.add(back_button)

        # 🔹 Envolver tudo no ScrollContainer
        self.main_window.content = toga.ScrollContainer(content=scroll_content)


    def save_settings(self, widget=None):
        """Salva as configurações, incluindo o número de botões e nomes das etapas."""
        for stage, inputs in self.settings_inputs.items():
            self.stages[stage]['nome'] = inputs['nome'].value
            self.stages[stage]['codigo'] = inputs['codigo'].value

        settings_data = {
            "num_buttons": self.num_buttons,  # 🔹 Salva o número de botões
            "stages": self.stages
        }

        with open(self.settings_file, "w") as f:
            json.dump(settings_data, f, indent=4)

        self.return_to_main(widget)


    def return_to_main(self, widget):
        """Volta para a tela principal e atualiza os botões conforme a configuração."""
        self.dynamic_content = self.create_dynamic_buttons()  # 🔹 Recria os botões
        self.main_window.content = toga.Box(
            children=[self.main_content_top, self.dynamic_content, self.main_content_bot],
            style=Pack(direction=COLUMN)
        )

    def view_logs(self, widget):
        """Exibe a interface de consulta de logs, garantindo que os detalhes apareçam logo abaixo do item selecionado."""
        if not os.path.exists(self.log_file):
            self.main_window.info_dialog("Logs", "Nenhum log encontrado.")
            return

        try:
            with open(self.log_file, "r") as f:
                self.logs = json.load(f)

            if not isinstance(self.logs, list):
                self.logs = []
        except (json.JSONDecodeError, ValueError):
            with open(self.log_file, "w") as f:
                json.dump([], f, indent=4)

            self.logs = []
            self.main_window.info_dialog("Erro nos Logs", "O arquivo de logs estava corrompido e foi resetado.")

        # 🔹 Container principal
        main_container = toga.Box(style=Pack(direction=COLUMN, flex=1, padding=10))

        # 🔹 Campo de busca
        search_box = toga.Box(style=Pack(direction=ROW, padding=10))
        self.search_input = toga.TextInput(
            placeholder="Buscar por data, token ou card JIRA",
            style=Pack(flex=1, padding=5)
        )
        search_button = toga.Button("Buscar", on_press=lambda widget: self.search_logs(widget) or self.prevent_scroll_on_click(), style=Pack(padding=5))
        search_box.add(self.search_input)
        search_box.add(search_button)

        back_button = toga.Button("Voltar", on_press=lambda widget: self.return_to_main(widget) or self.prevent_scroll_on_click(), style=Pack(padding=10))

        main_container.add(search_box)
        main_container.add(back_button)

        # 🔹 Container para resultados e detalhes
        self.results_box = toga.Box(style=Pack(direction=COLUMN, flex=1, padding=10))
        
        # 🔹 Adicionamos a área de resultados ao layout
        main_container.add(self.results_box)

        # 🔹 Envolve os resultados e detalhes dentro de um ScrollContainer
        self.main_window.content = toga.ScrollContainer(content=main_container)

    def search_logs(self, widget):
        """Filtra os logs e exibe os resultados na tela, garantindo que os detalhes apareçam logo abaixo."""
        query = self.search_input.value.strip()
        if not query:
            return

        filtered_logs = [
            log for log in self.logs
            if query in log["data_finalizacao"] or query in log["token"] or query in log["card_jira"]
        ]

        for child in self.results_box.children[:]:
            self.results_box.remove(child)

        if not filtered_logs:
            self.results_box.add(toga.Label("Nenhum resultado encontrado.", style=Pack(padding=10, color="red")))
            return

        for log in filtered_logs:
            log_box = toga.Box(style=Pack(direction=COLUMN, padding=8, background_color="#f5f5f5"))

            log_button = toga.Button(
                f"DATA: {log['data_finalizacao']} | CARD: {log['card_jira']}",
                on_press=functools.partial(self.display_log_details, log, log_box),
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

    def display_log_details(self, log, log_box, widget=None):
        """Exibe os detalhes do log abaixo do item clicado. Se já estiver aberto, fecha."""
        
        # 🔹 Se o log já estiver aberto, remove ele ao clicar novamente
        if hasattr(log_box, "details") and log_box.details:
            log_box.remove(log_box.details)
            log_box.details = None
            self.current_token = None  # 🔹 Reseta o token ao fechar o detalhe
            return

        self.current_token = log["token"]  # 🔹 Armazena o token do log atual

        details_container = toga.Box(style=Pack(direction=COLUMN, padding=10, background_color="#e0e0e0"))

        details_container.add(toga.Label(f"Card JIRA: {log['card_jira']}", style=Pack(padding=5, font_weight="bold")))
        details_container.add(toga.Label(f"Token: {log['token']}", style=Pack(padding=5)))
        details_container.add(toga.Label(f"Data: {log['data_finalizacao']}", style=Pack(padding=5)))

        header = toga.Box(style=Pack(direction=ROW, padding=5, background_color="#dcdcdc"))
        header.add(toga.Label("Etapa", style=Pack(flex=1, padding=5, font_weight="bold")))
        header.add(toga.Label("Código", style=Pack(flex=1, padding=5, font_weight="bold")))
        header.add(toga.Label("Tempo", style=Pack(flex=1, padding=5, font_weight="bold")))
        
        details_container.add(header)

        for etapa in log["etapas"]:
            row = toga.Box(style=Pack(direction=ROW, padding=5))
            row.add(toga.Label(etapa["etapa"], style=Pack(flex=1, padding=5)))
            row.add(toga.Label(etapa["codigo"], style=Pack(flex=1, padding=5)))

            tempo_minutos = math.ceil(etapa["tempo"] / 60)
            row.add(toga.Label(f"{tempo_minutos} minuto(s)", style=Pack(flex=1, padding=5)))

            details_container.add(row)

        edit_button = toga.Button(
            "Editar",
            on_press=lambda widget: self.show_detailed_edit_view(log, details_container),
            style=Pack(padding=10, background_color="#FFC107", color="black")
        )
        
        details_container.add(edit_button)

        log_box.details = details_container  # Marca que o log já tem um detalhe aberto
        log_box.add(details_container)

    def show_detailed_edit_view(self, log, details_container):
        """Mostra todas as ocorrências individuais para edição em ordem cronológica. Se já estiver aberta, fecha."""

        # 🔹 Se a edição já estiver aberta, fecha ao clicar novamente
        if hasattr(details_container, "edit_box") and details_container.edit_box:
            details_container.remove(details_container.edit_box)
            details_container.edit_box = None
            return

        # 🔹 Criamos um container para os detalhes
        edit_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # 🔹 Cabeçalho da edição
        header = toga.Box(style=Pack(direction=ROW, padding=5, background_color='#dcdcdc'))
        header.add(toga.Label("Etapa", style=Pack(flex=1, padding=5, font_weight="bold")))
        header.add(toga.Label("Código", style=Pack(flex=1, padding=5, font_weight="bold")))
        header.add(toga.Label("Início", style=Pack(flex=2, padding=5, font_weight="bold")))
        header.add(toga.Label("Fim", style=Pack(flex=2, padding=5, font_weight="bold")))
        header.add(toga.Label("Tempo (segundos)", style=Pack(flex=1, padding=5, font_weight="bold")))

        edit_box.add(header)

        # 🔹 Criar campos editáveis para cada entrada individual
        self.edit_inputs = []
        for etapa in log["etapas"]:
            row = toga.Box(style=Pack(direction=ROW, padding=5))

            etapa_label = toga.Label(etapa["etapa"], style=Pack(flex=1, padding=5))
            codigo_label = toga.Label(etapa["codigo"], style=Pack(flex=1, padding=5))
            inicio_input = toga.TextInput(value=etapa["inicio"], style=Pack(flex=2, padding=5))
            fim_input = toga.TextInput(value=etapa["fim"], style=Pack(flex=2, padding=5))

            # 🔹 Mantemos o tempo em segundos para edição
            tempo_label = toga.Label(f"{etapa['tempo']} segundo(s)", style=Pack(flex=1, padding=5))

            # 🔹 Guarda os inputs para edição
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
            edit_box.add(row)

            # 🔹 Atualiza o tempo automaticamente ao alterar os valores de início e fim
            inicio_input.on_change = lambda widget: self.update_time(inicio_input, fim_input, tempo_label)
            fim_input.on_change = lambda widget: self.update_time(inicio_input, fim_input, tempo_label)

        # 🔹 Botão "Salvar Alterações"
        save_button = toga.Button(
            "Salvar Alterações",
            ##on_press=lambda widget: self.save_edited_log(widget) or self.prevent_scroll_on_click(),
            on_press=lambda widget: (self.save_edited_log(widget), self.prevent_scroll_on_click()),
            style=Pack(padding=10, background_color="#4CAF50", color="white", flex=1)
        )

        edit_box.add(save_button)

        # 🔹 Exibe os detalhes na tela abaixo do resumo do log
        details_container.edit_box = edit_box  # Marca que a edição já foi aberta
        details_container.add(edit_box)

    def prevent_scroll_on_click(self):
        """Mantém a posição de rolagem ao interagir com botões."""
        try:
            # Obtém a posição atual da rolagem
            scroll_position = self.main_window.content.style.padding_top
            # Define um pequeno atraso e restaura a posição após a ação
            toga.App.set_timeout(0.1, lambda: setattr(self.main_window.content.style, "padding_top", scroll_position))
        except AttributeError:
            pass  # Se não for possível acessar, ignora o erro


    def save_edited_log(self, widget):
        """Salva as edições feitas nos detalhes do log e remove linhas vazias."""
        
        if not hasattr(self, "current_token") or not self.current_token:
            self.main_window.info_dialog("Erro", "Nenhum log foi selecionado para edição.")
            return

        with open(self.log_file, "r") as f:
            logs = json.load(f)

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
                            tempo_total = 0

                        if inicio != "00:00:00" or fim != "00:00:00":
                            novas_etapas.append({
                                "etapa": etapa["etapa"],
                                "codigo": etapa["codigo"],
                                "inicio": inicio,
                                "fim": fim,
                                "tempo": tempo_total
                            })

                log["etapas"] = novas_etapas

        with open(self.log_file, "w") as f:
            json.dump(logs, f, indent=4)

        self.main_window.info_dialog("Sucesso", "Log atualizado com sucesso!")
        self.current_token = None  # 🔹 Reseta o token após salvar

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

        # Desativar botões e configurações enquanto uma etapa está ativa
        self.logs_button.enabled = False
        self.finish_button.enabled = True

        # Desativar o menu de configurações
        for command in self.main_window.toolbar:
            command.enabled = False  # 🔹 Desativa os comandos do menu

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

    def format_time(self, seconds):
        """Converte segundos para minutos, sempre arredondando para cima."""
        minutes = math.ceil(seconds / 60)  # 🔹 Sempre arredonda para cima
        return f"{minutes} minuto(s)"

    def finish_tracking(self, widget):
        """Finaliza a contagem de tempo, salva os logs e reativa os botões e menus."""
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

        # Reativar os botões e configurações
        self.logs_button.enabled = True
        self.finish_button.enabled = False

        for command in self.main_window.toolbar:
            command.enabled = True  # 🔹 Reativa os comandos do menu

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

        # 🔹 Exibir o resumo com tempos em minutos
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

        # Resetar botões (remover cores de seleção)
        for button in self.buttons.values():
            del button.style.background_color

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
    return TimeTrackerApp("Time Tracker v1.1", "com.viniciustorres.timetracker")