import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
import os
import json
import time
from datetime import datetime
import uuid

class TimeTrackerApp(toga.App):
    def startup(self):
        """Inicializa o aplicativo."""
        # Janela principal
        self.main_window = toga.MainWindow(title=self.formal_name)

        # Inicializar pastas e arquivos
        self.log_folder = "logs"
        os.makedirs(self.log_folder, exist_ok=True)
        self.settings_file = os.path.join(self.log_folder, "settings.json")
        self.log_file = os.path.join(self.log_folder, "tracking_logs.json")

        # Carregar configurações de etapas e códigos
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

        # Garantir que todas as etapas têm a chave 'tempos'
        for stage in self.stages.values():
            if "tempos" not in stage:
                stage["tempos"] = []

        # Variáveis para controle de tempo
        self.current_stage = None
        self.start_time = None

        # Campo para Card JIRA
        jira_label = toga.Label("Card JIRA:", style=Pack(padding=5))
        self.jira_input = toga.TextInput(placeholder="Digite o card JIRA (ex: EVOO-352)", style=Pack(flex=1, padding=5))
        jira_box = toga.Box(children=[jira_label, self.jira_input], style=Pack(direction=ROW, padding=10))

        # Label para tempo total
        self.time_label = toga.Label("Tempo total: 0 segundos", style=Pack(padding=10))

        # Botões das etapas
        self.buttons = {}
        button_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        row = None
        for i, (stage_name, stage_data) in enumerate(self.stages.items()):
            button = toga.Button(
                stage_data["nome"],
                style=Pack(flex=1, padding=5),
                on_press=self.handle_stage,
                id=stage_name
            )
            self.buttons[stage_name] = button
            if i % 2 == 0:
                row = toga.Box(style=Pack(direction=ROW, padding=5))
                button_box.add(row)
            row.add(button)

        # Botão para finalizar
        finish_button = toga.Button(
            "Finalizar",
            style=Pack(padding=10),
            on_press=self.finish_tracking
        )
        button_box.add(finish_button)

        # Botão para consultar logs
        logs_button = toga.Button(
            "Consultar Logs",
            style=Pack(padding=10),
            on_press=self.view_logs
        )
        button_box.add(logs_button)

        # Layout principal
        layout = toga.Box(
            children=[jira_box, self.time_label, button_box],
            style=Pack(direction=COLUMN, padding=10)
        )

        # Menu Help > Configurações
        help_menu = toga.Group("Configurações")
        settings_command = toga.Command(
            self.open_settings,
            text="Configurações",
            group=help_menu
        )
        self.commands.add(settings_command)

        # Configurar janela principal
        self.main_window.content = layout
        self.main_window.show()

    def handle_stage(self, widget):
        """Gerencia a seleção de etapas e o tempo registrado."""
        now = time.time()

        if self.current_stage:
            # Finaliza o tempo da etapa anterior
            elapsed = now - self.start_time
            self.stages[self.current_stage]["tempos"].append(elapsed)
            del self.buttons[self.current_stage].style.background_color

        # Atualiza para a nova etapa
        self.current_stage = widget.id
        self.start_time = now
        widget.style.background_color = "lightblue"

    def format_time(self, seconds):
        """Formata o tempo em minutos e segundos."""
        if seconds < 60:
            return f"{int(seconds)} segundos"
        else:
            minutes = seconds // 60
            return f"{int(minutes)} minutos"

    def save_log(self, token, jira_card, resumo):
        """Salva as informações em um arquivo de log."""
        log_data = {
            "token": token,
            "data_finalizacao": datetime.now().strftime("%d/%m/%Y"),
            "card_jira": jira_card,
            "etapas": [
                {"etapa": etapa, "codigo": codigo, "tempo": int(sum(data["tempos"]))}
                for etapa, codigo, data in resumo
            ]
        }

        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                logs = json.load(f)
        else:
            logs = []

        logs.append(log_data)

        with open(self.log_file, "w") as f:
            json.dump(logs, f, indent=4)

    def finish_tracking(self, widget):
        """Finaliza o acompanhamento, exibe o resumo e reseta o estado."""
        if self.current_stage:
            # Finaliza a etapa atual
            elapsed = time.time() - self.start_time
            self.stages[self.current_stage]["tempos"].append(elapsed)

        # Gerar resumo
        jira_card = self.jira_input.value.strip() or "SEM CARD JIRA"
        total_time = sum(sum(stage["tempos"]) for stage in self.stages.values())
        resumo = [
            (data['nome'], data['codigo'], data)
            for data in self.stages.values() if sum(data['tempos']) > 0
        ]

        # Criar nova janela para exibir o resumo
        resumo_window = toga.Window(title="Resumo do Acompanhamento")
        token = uuid.uuid4().hex

        header = toga.Box(
            children=[
                toga.Label(f"Card JIRA: {jira_card}", style=Pack(padding=5, font_weight="bold")),
                toga.Label(f"Token: {token}", style=Pack(padding=5, font_weight="bold"))
            ],
            style=Pack(direction=COLUMN, padding=10)
        )

        table = toga.Box(style=Pack(direction=COLUMN, padding=10))

        header_row = toga.Box(style=Pack(direction=ROW, padding=5, background_color='#f0f0f0'))
        header_row.add(toga.Label("Etapa", style=Pack(width=150, padding=5, font_weight="bold")))
        header_row.add(toga.Label("Código", style=Pack(width=100, padding=5, font_weight="bold")))
        header_row.add(toga.Label("Tempo", style=Pack(width=150, padding=5, font_weight="bold")))
        table.add(header_row)

        for etapa, codigo, data in resumo:
            row = toga.Box(style=Pack(direction=ROW, padding=5))
            row.add(toga.Label(etapa, style=Pack(width=150, padding=5)))
            row.add(toga.Label(codigo, style=Pack(width=100, padding=5)))
            row.add(toga.Label(self.format_time(sum(data["tempos"])), style=Pack(width=150, padding=5)))
            table.add(row)

        total_label = toga.Label(f"Tempo Total: {self.format_time(total_time)}", style=Pack(padding=10))

        close_button = toga.Button(
            "Fechar",
            on_press=lambda x: resumo_window.close(),
            style=Pack(padding=10, alignment=CENTER)
        )

        resumo_layout = toga.Box(
            children=[header, table, total_label, close_button],
            style=Pack(direction=COLUMN, padding=20)
        )

        resumo_window.content = resumo_layout
        self.windows.add(resumo_window)
        resumo_window.show()

        # Salvar log
        self.save_log(token, jira_card, resumo)

        # Resetar estados
        for stage in self.stages.values():
            stage["tempos"] = []
        self.current_stage = None
        self.start_time = None
        for button in self.buttons.values():
            del button.style.background_color
        self.jira_input.value = ""
        self.time_label.text = "Tempo total: 0 segundos"

    def filter_logs(self, query, table):
        """Filtra os logs com base na consulta."""
        if not os.path.exists(self.log_file):
            return

        with open(self.log_file, "r") as f:
            logs = json.load(f)

        filtered_logs = [
            log for log in logs
            if query in log["data_finalizacao"]
            or query in log["token"]
            or query in log["card_jira"]
        ]

        # Limpa o conteúdo atual da tabela recriando-a
        for child in table.children[:]:
            table.remove(child)

        # Adicionar cabeçalho novamente
        header_row = toga.Box(style=Pack(direction=ROW, padding=5, background_color='#f0f0f0'))
        header_row.add(toga.Label("Data", style=Pack(width=150, padding=5, font_weight="bold")))
        header_row.add(toga.Label("Token", style=Pack(width=200, padding=5, font_weight="bold")))
        header_row.add(toga.Label("Card JIRA", style=Pack(width=150, padding=5, font_weight="bold")))
        header_row.add(toga.Label("Editar", style=Pack(width=100, padding=5, font_weight="bold")))
        table.add(header_row)

        # Adicionar os logs filtrados
        for log in filtered_logs:
            row = toga.Box(style=Pack(direction=ROW, padding=5))
            row.add(toga.Label(log["data_finalizacao"], style=Pack(width=150, padding=5)))
            row.add(toga.Label(log["token"], style=Pack(width=200, padding=5)))
            row.add(toga.Label(log["card_jira"], style=Pack(width=150, padding=5)))
            edit_button = toga.Button(
                "Editar",
                on_press=lambda x, log=log: self.edit_log(log,table),
                style=Pack(width=100, padding=5)
            )
            row.add(edit_button)
            table.add(row)


    def view_logs(self, widget):
        """Abre uma janela para consultar os logs."""
        if not os.path.exists(self.log_file):
            self.main_window.info_dialog("Logs", "Nenhum log encontrado.")
            return

        with open(self.log_file, "r") as f:
            logs = json.load(f)

        logs_window = toga.Window(title="Logs Salvos")

        search_box = toga.Box(style=Pack(direction=ROW, padding=10))
        search_input = toga.TextInput(placeholder="Buscar por data, token ou card JIRA", style=Pack(flex=1, padding=5))
        search_button = toga.Button(
            "Buscar",
            on_press=lambda x: self.filter_logs(search_input.value, table),
            style=Pack(padding=5)
        )
        search_box.add(search_input)
        search_box.add(search_button)

        table = toga.Box(style=Pack(direction=COLUMN, padding=10))

        header_row = toga.Box(style=Pack(direction=ROW, padding=5, background_color='#f0f0f0'))
        header_row.add(toga.Label("Data", style=Pack(width=150, padding=5, font_weight="bold")))
        header_row.add(toga.Label("Token", style=Pack(width=200, padding=5, font_weight="bold")))
        header_row.add(toga.Label("Card JIRA", style=Pack(width=150, padding=5, font_weight="bold")))
        header_row.add(toga.Label("Editar", style=Pack(width=100, padding=5, font_weight="bold")))
        table.add(header_row)

        for log in logs:
            row = toga.Box(style=Pack(direction=ROW, padding=5))
            row.add(toga.Label(log["data_finalizacao"], style=Pack(width=150, padding=5)))
            row.add(toga.Label(log["token"], style=Pack(width=200, padding=5)))
            row.add(toga.Label(log["card_jira"], style=Pack(width=150, padding=5)))
            edit_button = toga.Button(
                "Editar",
                on_press=lambda x, log=log: self.edit_log(log,table),
                style=Pack(width=100, padding=5)
            )
            row.add(edit_button)
            table.add(row)

        close_button = toga.Button(
            "Fechar",
            on_press=lambda x: logs_window.close(),
            style=Pack(padding=10, alignment=CENTER)
        )

        logs_layout = toga.Box(
            children=[search_box, table, close_button],
            style=Pack(direction=COLUMN, padding=20)
        )

        logs_window.content = logs_layout
        self.windows.add(logs_window)
        logs_window.show()

    def open_settings(self, widget):
        """Abre a janela de configurações para personalizar etapas e códigos."""
        self.settings_window = toga.Window(title="Configurações")
        settings_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        self.settings_inputs = {}  # Armazenar os inputs de cada configuração
        for i, (stage, data) in enumerate(self.stages.items()):
            # Label da Etapa
            stage_label = toga.Label(f"Etapa {i+1}:", style=Pack(padding=5))

            # Input para o Nome da Etapa
            name_input = toga.TextInput(
                value=data["nome"],
                style=Pack(flex=1, padding=5)
            )

            # Input para o Código da Etapa
            code_input = toga.TextInput(
                value=data["codigo"],
                style=Pack(flex=1, padding=5)
            )

            # Adicionar os campos à estrutura
            self.settings_inputs[stage] = {"nome": name_input, "codigo": code_input}

            # Layout de cada linha
            row = toga.Box(
                children=[stage_label, name_input, code_input],
                style=Pack(direction=ROW, padding=5)
            )
            settings_box.add(row)

        # Botão Salvar
        save_button = toga.Button(
            "Salvar",
            on_press=self.save_settings,
            style=Pack(padding=10, alignment=CENTER)
        )
        settings_box.add(save_button)

        self.settings_window.content = settings_box
        self.settings_window.show()


    def update_stage_buttons(self):
        """Atualiza os botões das etapas na interface principal."""
        # Obter o container de botões
        button_box = self.main_window.content.children[2]  # Obtém o container dos botões

        # Identificar os botões existentes de "Finalizar" e "Consultar Logs"
        finish_button = next((child for child in button_box.children if getattr(child, "text", "") == "Finalizar"), None)
        logs_button = next((child for child in button_box.children if getattr(child, "text", "") == "Consultar Logs"), None)

        # Limpar os botões relacionados às etapas
        for child in list(button_box.children):
            if isinstance(child, toga.Box) and child not in [finish_button, logs_button]:
                button_box.remove(child)

        # Reconstruir os botões das etapas
        row = None
        for i, (stage_name, stage_data) in enumerate(self.stages.items()):
            button = toga.Button(
                stage_data["nome"],
                style=Pack(flex=1, padding=5),
                on_press=self.handle_stage,
                id=stage_name
            )
            self.buttons[stage_name] = button
            if i % 2 == 0:
                row = toga.Box(style=Pack(direction=ROW, padding=5))
                button_box.insert(-2, row)  # Insere antes dos dois últimos botões fixos
            row.add(button)

    def save_settings(self, widget):
        """Salva as configurações personalizadas."""
        for stage, inputs in self.settings_inputs.items():
            self.stages[stage]["nome"] = inputs["nome"].value
            self.stages[stage]["codigo"] = inputs["codigo"].value

        # Salvar no arquivo JSON
        with open(self.settings_file, "w") as f:
            json.dump(self.stages, f, indent=4)

        # Atualizar os botões na interface principal
        self.update_stage_buttons()

        self.settings_window.close()
        self.main_window.info_dialog("Sucesso", "Configurações salvas com sucesso!")

    def edit_log(self, log, table):
        """Abre uma janela para editar os detalhes de um log."""
        edit_window = toga.Window(title="Editar Log")

        form = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # Campo para editar o nome do card JIRA
        jira_box = toga.Box(style=Pack(direction=ROW, padding=5))
        jira_label = toga.Label("Card JIRA:", style=Pack(padding=5))
        jira_input = toga.TextInput(value=log["card_jira"], style=Pack(flex=1, padding=5))
        jira_box.add(jira_label)
        jira_box.add(jira_input)

        form.add(jira_box)

        etapas_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        etapas_box.add(toga.Label("Editar Etapas", style=Pack(padding=5, font_weight="bold")))

        etapa_inputs = []
        for etapa in log["etapas"]:
            row = toga.Box(style=Pack(direction=ROW, padding=5))
            nome_input = toga.TextInput(value=etapa["etapa"], style=Pack(flex=1, padding=5))
            codigo_input = toga.TextInput(value=etapa["codigo"], style=Pack(flex=1, padding=5))
            tempo_input = toga.TextInput(value=str(etapa["tempo"]), style=Pack(flex=1, padding=5))
            etapa_inputs.append({"nome": nome_input, "codigo": codigo_input, "tempo": tempo_input})
            row.add(nome_input)
            row.add(codigo_input)
            row.add(tempo_input)
            etapas_box.add(row)

        save_button = toga.Button(
            "Salvar Alterações",
            on_press=lambda x: self.save_edited_log(log, etapa_inputs, jira_input, edit_window, table),
            style=Pack(padding=10, alignment=CENTER)
        )

        form.add(etapas_box)
        form.add(save_button)

        edit_window.content = form
        self.windows.add(edit_window)
        edit_window.show()

    def update_table(self, table, logs):
        """Atualiza a tabela com os dados mais recentes."""
        # Limpa o conteúdo atual da tabela
        for child in table.children[:]:
            table.remove(child)

        # Adiciona cabeçalho
        header_row = toga.Box(style=Pack(direction=ROW, padding=5, background_color='#f0f0f0'))
        header_row.add(toga.Label("Data", style=Pack(width=150, padding=5, font_weight="bold")))
        header_row.add(toga.Label("Token", style=Pack(width=200, padding=5, font_weight="bold")))
        header_row.add(toga.Label("Card JIRA", style=Pack(width=150, padding=5, font_weight="bold")))
        header_row.add(toga.Label("Editar", style=Pack(width=100, padding=5, font_weight="bold")))
        table.add(header_row)

        # Adiciona os logs atualizados
        for log in logs:
            row = toga.Box(style=Pack(direction=ROW, padding=5))
            row.add(toga.Label(log["data_finalizacao"], style=Pack(width=150, padding=5)))
            row.add(toga.Label(log["token"], style=Pack(width=200, padding=5)))
            row.add(toga.Label(log["card_jira"], style=Pack(width=150, padding=5)))
            edit_button = toga.Button(
                "Editar",
                on_press=lambda x, log=log: self.edit_log(log, table),
                style=Pack(width=100, padding=5)
            )
            row.add(edit_button)
            table.add(row)

    def save_edited_log(self, log, etapa_inputs, jira_input, edit_window, table):
        """Salva as alterações feitas em um log e atualiza a tabela."""
        # Atualizar o nome do card JIRA
        log["card_jira"] = jira_input.value.strip()

        # Atualizar os dados do log com os inputs
        for etapa, inputs in zip(log["etapas"], etapa_inputs):
            etapa["etapa"] = inputs["nome"].value
            etapa["codigo"] = inputs["codigo"].value
            try:
                etapa["tempo"] = int(inputs["tempo"].value)
            except ValueError:
                etapa["tempo"] = 0

        # Carregar todos os logs
        with open(self.log_file, "r") as f:
            logs = json.load(f)

        # Encontrar o log pelo token e atualizá-lo
        for existing_log in logs:
            if existing_log["token"] == log["token"]:
                existing_log.update(log)
                break

        # Salvar os logs atualizados
        with open(self.log_file, "w") as f:
            json.dump(logs, f, indent=4)

        # Atualizar a tabela na interface
        self.update_table(table, logs)

        edit_window.close()
        self.main_window.info_dialog("Sucesso", "Log atualizado com sucesso!")

def main():
    return TimeTrackerApp("Time Tracker", "com.viniciustorres.timetracker")
