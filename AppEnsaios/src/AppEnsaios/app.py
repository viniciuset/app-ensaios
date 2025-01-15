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
            (data['nome'], data['codigo'], self.format_time(sum(data['tempos'])))
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

        for etapa, codigo, tempo in resumo:
            row = toga.Box(style=Pack(direction=ROW, padding=5))
            row.add(toga.Label(etapa, style=Pack(width=150, padding=5)))
            row.add(toga.Label(codigo, style=Pack(width=100, padding=5)))
            row.add(toga.Label(tempo, style=Pack(width=150, padding=5)))
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

        # Resetar estados
        for stage in self.stages.values():
            stage["tempos"] = []
        self.current_stage = None
        self.start_time = None
        for button in self.buttons.values():
            del button.style.background_color
        self.jira_input.value = ""
        self.time_label.text = "Tempo total: 0 segundos"

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

    def save_settings(self, widget):
        """Salva as configurações personalizadas."""
        for stage, inputs in self.settings_inputs.items():
            self.stages[stage]["nome"] = inputs["nome"].value
            self.stages[stage]["codigo"] = inputs["codigo"].value

        # Salvar no arquivo JSON
        with open(self.settings_file, "w") as f:
            json.dump(self.stages, f)

        self.settings_window.close()

def main():
    return TimeTrackerApp("Time Tracker", "com.viniciustorres.timetracker")
