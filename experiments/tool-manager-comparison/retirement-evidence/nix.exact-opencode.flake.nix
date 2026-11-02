{
  description = "Task-local probe of locked Nix routes for SCORE's existing apm/opencode pins";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.nixpkgsAlternate.url = "github:NixOS/nixpkgs/nixos-25.11";
  outputs = { nixpkgs, ... }:
    let
      systems = [ "x86_64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in {
      candidateVersions = forAllSystems (system:
        let pkgs = import nixpkgs { inherit system; };
        in builtins.listToAttrs (map (name: {
          inherit name;
          value = if builtins.hasAttr name pkgs
            then (builtins.getAttr name pkgs).version
            else "MISSING";
        }) [ "apm" "apm-cli" "opencode" ]));
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          opencodeExact = pkgs.stdenvNoCC.mkDerivation {
            pname = "opencode";
            version = "2.2.3";
            src = pkgs.fetchurl {
              name = "opencode-linux-x64-2.2.3.tar.gz";
              url = "https://github.com/anomalyco/opencode/releases/download/v2.2.3/opencode-linux-x64.tar.gz";
              sha256 = "ef3aeeaf5522b10d69a3da7bbd6e6d8d259f845833d96b8310767d3407b18a35";
            };
            nativeBuildInputs = [ pkgs.autoPatchelfHook pkgs.makeWrapper pkgs.gnutar pkgs.gzip ];
            buildInputs = [ pkgs.stdenv.cc.cc.lib pkgs.wayland ];
            dontConfigure = true;
            dontBuild = true;
            # Bun embeds the application payload in the executable.
            dontStrip = true;
            dontUnpack = true;
            installPhase = ''
              mkdir -p "$TMPDIR/opencode-source"
              tar -xzf "$src" -C "$TMPDIR/opencode-source"
              install -Dm755 "$TMPDIR/opencode-source/opencode" "$out/bin/opencode"
              wrapProgram "$out/bin/opencode" \
                --set OPENCODE_DISABLE_AUTOUPDATE true \
                --suffix PATH : ${pkgs.lib.makeBinPath [ pkgs.ripgrep ]}
            '';
            meta.mainProgram = "opencode";
          };
        in {
          apm = pkgs.apm-cli;
          opencode = pkgs.opencode;
          opencodeExact = opencodeExact;
        });
      legacyPackages = forAllSystems (system: import nixpkgs { inherit system; });
    };
}
