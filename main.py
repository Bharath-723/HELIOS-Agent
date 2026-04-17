"""HELIOS - CLI Mode. Run: python main.py"""
import sys

def main():
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Prompt
        console = Console()
        console.print(Panel(
            "[bold yellow]HELIOS[/bold yellow] — Autonomous Desktop Agent\n"
            "[dim cyan]Offline-First · Hybrid AI (Mistral/Gemma + GPT)[/dim cyan]",
            border_style="yellow", padding=(1,4)))
        console.print("[dim]Type [bold]exit[/bold] to quit · [bold]help[/bold] for commands[/dim]\n")
        ask = lambda: Prompt.ask("[bold orange1]You[/bold orange1]")
        say = lambda r: console.print(f"\n[bold cyan]HELIOS:[/bold cyan] {r}\n")
    except ImportError:
        def ask(): return input("You: ")
        def say(r): print(f"\nHELIOS: {r}\n")

    from agent import HELIOSAgent
    try:
        agent = HELIOSAgent()
        say("Ready! How can I help?")
    except Exception as e:
        print(f"Failed to start: {e}")
        print("Make sure Ollama is running: ollama serve")
        sys.exit(1)

    HELP = """
Commands:
  play <movie/song>              Open and play media
  open <app>                     Launch an application
  close/kill <app>               Close an application
  search youtube <query>         Search YouTube
  search google <query>          Search Google
  open gmail                     Open Gmail
  compose mail to <email>...     Compose email
  create file <name> on desktop  Create a file
  wifi on/off                    Toggle WiFi
  bluetooth on/off               Toggle Bluetooth
  airplane mode on/off           Toggle Airplane mode
  brightness up/down/set <n>     Control brightness
  volume up/down/mute            Control volume
  dark mode on/off               Toggle dark mode
  battery saver/performance      Power plan
  screenshot                     Take screenshot
  lock screen                    Lock PC
  system info                    System status
  battery status                 Battery info
  disk space                     Storage info
  what's running                 List running apps
  create note about <topic>      Create a note
  remind me in <time> to <task>  Set reminder
  help                           This menu
  exit                           Quit
"""
    while True:
        try:
            user = ask().strip()
        except (KeyboardInterrupt, EOFError):
            say("Goodbye!")
            agent.shutdown()
            break
        if user.lower() in ("exit", "quit", "bye"):
            say("Goodbye!")
            agent.shutdown()
            break
        if user.lower() == "help":
            print(HELP); continue
        if not user: continue
        try:
            say(agent.process(user))
        except Exception as e:
            say(f"Error: {e}")

if __name__ == "__main__":
    main()
