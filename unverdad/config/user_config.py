import dataclasses
import pathlib

import schemaspec
from unverdad.config import constants


@dataclasses.dataclass
class SettingsSpec:
    mods_home: pathlib.Path = dataclasses.field(
        default=constants.DATA_HOME / "mods",
        metadata=schemaspec.SchemaItemField(
            possible_values=(schemaspec.PathAdapter(),),
            description="mods import destination.",
        ).metadata(),
    )

    @dataclasses.dataclass
    class DefaultGameSpec:
        name: str = dataclasses.field(
            default="Guilty Gear Strive",
            metadata=schemaspec.SchemaItemField(
                possible_values=(schemaspec.StringAdapter(),),
                description="name of the game",
            ).metadata(),
        )
        enabled: bool = dataclasses.field(
            default=True,
            metadata=schemaspec.SchemaItemField(
                possible_values=(schemaspec.BoolAdapter(),),
                description="whether or not default_game should be used at all.",
            ).metadata(),
        )

    default_game: DefaultGameSpec = dataclasses.field(
        default_factory=DefaultGameSpec,
        metadata=schemaspec.SchemaTableField(
            description="table of game settings where each game is all lowercase",
        ).metadata(),
    )

    @dataclasses.dataclass
    class PredefinedGamesSpec:
        @dataclasses.dataclass
        class GameSpec:
            game_path: pathlib.Path = dataclasses.field(
                default=pathlib.Path(
                    "~/.steam/root/steamapps/common/GUILTY GEAR STRIVE/"
                ),
                metadata=schemaspec.SchemaItemField(
                    possible_values=(schemaspec.PathAdapter(),),
                    description="game install path.",
                ).metadata(),
            )

        guilty_gear_strive: GameSpec = dataclasses.field(
            default_factory=lambda x=GameSpec: x(
                game_path=pathlib.Path(
                    "~/.steam/root/steamapps/common/GUILTY GEAR STRIVE/"
                )
            ),
            metadata=schemaspec.SchemaItemField(
                possible_values=(schemaspec.schema_from(GameSpec),),
                description="GUILTY GEAR STRIVE options",
            ).metadata(),
        )

    games: PredefinedGamesSpec = dataclasses.field(
        default_factory=PredefinedGamesSpec,
        metadata=schemaspec.SchemaTableField(
            description="table of game settings where each game is all lowercase",
        ).metadata(),
    )


SCHEMA: schemaspec.Schema = schemaspec.schema_from(SettingsSpec)
SETTINGS: SettingsSpec = (
    SCHEMA.load_toml(constants.CONFIG_FILE)
    if constants.CONFIG_FILE.is_file()
    else SettingsSpec()
)
