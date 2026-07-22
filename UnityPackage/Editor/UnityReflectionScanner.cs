using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEngine;

namespace AIEngineer.Reflection
{
    [InitializeOnLoad]
    public static class ReflectionBoot
    {
        static ReflectionBoot()
        {
            Debug.Log("[AI] UnityReflectionScanner Loaded");
        }
    }

    [Serializable]
    public class ReflectionTypeInfo
    {
        public string assembly;
        public string namespaceName;
        public string className;
        public string baseClass;

        public List<string> methods =
            new List<string>();

        public List<string> properties =
            new List<string>();

        public List<string> fields =
            new List<string>();
    }

    [Serializable]
    public class ReflectionDatabase
    {
        public List<ReflectionTypeInfo> types =
            new List<ReflectionTypeInfo>();
    }

    public static class UnityReflectionScanner
    {
        public static void ExportReflection()
        {
            Debug.Log("[AI] Export Reflection Started");

            ReflectionDatabase database =
                new ReflectionDatabase();

            foreach
            (
                Assembly assembly
                in AppDomain.CurrentDomain.GetAssemblies()
            )
            {
                Type[] types;

                try
                {
                    types =
                        assembly.GetTypes();
                }
                catch
                {
                    continue;
                }

                foreach(Type type in types)
                {
                    if(type==null)
                        continue;

                    ReflectionTypeInfo info =
                        new ReflectionTypeInfo();

                    info.assembly =
                        assembly.GetName().Name;

                    info.namespaceName =
                        type.Namespace ?? "";

                    info.className =
                        type.Name;

                    info.baseClass =
                        type.BaseType!=null
                        ? type.BaseType.FullName
                        : "";

                    foreach(MethodInfo m in type.GetMethods())
                        info.methods.Add(m.Name);

                    foreach(PropertyInfo p in type.GetProperties())
                        info.properties.Add(p.Name);

                    foreach(FieldInfo f in type.GetFields())
                        info.fields.Add(f.Name);

                    database.types.Add(info);
                }
            }

            string folder =
                Path.Combine(
                    Application.dataPath,
                    "../AIReflection"
                );

            Directory.CreateDirectory(folder);

            string file =
                Path.Combine(
                    folder,
                    "unity_reflection.json"
                );

            File.WriteAllText(

                file,

                JsonUtility.ToJson(
                    database,
                    true
                )

            );

            Debug.Log(
                "[AI] Reflection Saved -> "
                + file
            );

            EditorUtility.RevealInFinder(
                file
            );
        }
    }
}
