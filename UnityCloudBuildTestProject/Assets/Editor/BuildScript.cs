using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace CloudBuildTest.Editor
{
    public static class BuildScript
    {
        [MenuItem("Assets/Save As Prefab", true)]
        private static bool SaveAsPrefabValidate() => Selection.activeGameObject != null;

        [MenuItem("Assets/Save As Prefab")]
        public static void SaveAsPrefab()
        {
            var go = Selection.activeGameObject;
            var folder = "Assets/Prefabs";

            if (!AssetDatabase.IsValidFolder(folder))
                AssetDatabase.CreateFolder("Assets", "Prefabs");

            var path = $"{folder}/{go.name}.prefab";
            PrefabUtility.SaveAsPrefabAsset(go, path);
            AssetDatabase.Refresh();
            Debug.Log($"Prefab saved: {path}");
        }

        [MenuItem("Build/Build Dedicated Server (Linux)")]
        public static void BuildDedicatedServer()
        {
            string[] scenes = EditorBuildSettings.scenes
                .Where(s => s.enabled)
                .Select(s => s.path)
                .ToArray();

            var options = new BuildPlayerOptions
            {
                scenes = scenes,
                locationPathName = "Builds/DedicatedServer/Server.x86_64",
                target = BuildTarget.StandaloneLinux64,
                subtarget = (int)StandaloneBuildSubtarget.Server,
                options = BuildOptions.None,
            };

            var report = BuildPipeline.BuildPlayer(options);
            Debug.Log($"Build result: {report.summary.result}");
        }
    }
}
