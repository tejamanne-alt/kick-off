using System.Collections.Generic;
using System.IO;
using DribbleToSchool.EditorTools;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The ball shells' geometry (Editor/BallShellGeometry, docs/LEARNINGS.md E18): a model's surfaces are found where they cross
    /// the ball's plane, and the cells merged into boxes that cover exactly those cells.
    /// </summary>
    public class BallShellTests
    {
        [Test]
        public void ATriangleIsClippedToTheBallsPlane()
        {
            // Far behind or in front of the plane: nothing.
            Assert.AreEqual(0, BallShellGeometry.ClipToSlab(new Vector3(0, 0, 1), new Vector3(1, 0, 1), new Vector3(0, 1, 2)).Count);
            Assert.AreEqual(0, BallShellGeometry.ClipToSlab(new Vector3(0, 0, -1), new Vector3(1, 0, -1), new Vector3(0, 1, -2)).Count);
            // Lying in the plane: all of it.
            Assert.AreEqual(3, BallShellGeometry.ClipToSlab(new Vector3(0, 0, 0), new Vector3(1, 0, 0), new Vector3(0, 1, 0)).Count);
            // Crossing it, like the side of the sweeper's cab: cut at both faces of the slab, nothing outside them.
            var cut = BallShellGeometry.ClipToSlab(new Vector3(1, 0, -1), new Vector3(1, 2, -1), new Vector3(1, 0, 1));
            Assert.Greater(cut.Count, 2);
            foreach (var p in cut) Assert.LessOrEqual(Mathf.Abs(p.z), BallShellGeometry.Slab + 1e-5f);
        }

        [Test]
        public void ASurfaceSeenEdgeOnStillMarksItsLine()
        {
            // A box's top, crossing the plane: in the street's x and y it is a line, with no inside. Its cells are still marked.
            var cells = new HashSet<Vector2Int>();
            BallShellGeometry.Rasterize(new List<Vector2> { new Vector2(0f, 1.2f), new Vector2(1f, 1.2f), new Vector2(1f, 1.2f), new Vector2(0f, 1.2f) }, cells);
            int row = Mathf.FloorToInt(1.2f / BallShellGeometry.Cell);
            for (int x = 0; x < Mathf.FloorToInt(1f / BallShellGeometry.Cell); x++)
                Assert.IsTrue(cells.Contains(new Vector2Int(x, row)), "cell " + x + " of the top's line");
        }

        [Test]
        public void CellsMergeIntoBoxesThatCoverExactlyThem()
        {
            // An L (a cab's front and its roof) and a stray cell.
            var cells = new HashSet<Vector2Int>();
            for (int y = 0; y < 10; y++) cells.Add(new Vector2Int(0, y));
            for (int x = 0; x < 6; x++) cells.Add(new Vector2Int(x, 10));
            cells.Add(new Vector2Int(20, 3));
            var boxes = BallShellGeometry.Merge(cells);
            var covered = new HashSet<Vector2Int>();
            foreach (var b in boxes)
                for (int y = b.y0; y <= b.y1; y++)
                    for (int x = b.x0; x <= b.x1; x++)
                        Assert.IsTrue(covered.Add(new Vector2Int(x, y)), "boxes overlap at " + x + "," + y);
            CollectionAssert.AreEquivalent(cells, covered);
            Assert.LessOrEqual(boxes.Count, 4, "a column, a row and a stray cell: a few boxes, not one a cell");
        }

        [Test]
        public void EveryLevelGetsItsBallShellsAndTheyLetTheKidPass()
        {
            string kit = File.ReadAllText(Path.Combine(Application.dataPath, "_Game/Scripts/Editor/LevelBuildKit.cs"));
            int finish = kit.IndexOf("public void Finish()");
            Assert.Greater(finish, 0);
            StringAssert.Contains("BuildBallShells", kit.Substring(finish, 1200), "every level's build ends with the ball shells");
            string shell = File.ReadAllText(Path.Combine(Application.dataPath, "_Game/Scripts/World/BallShell.cs"));
            StringAssert.Contains("Physics2D.IgnoreCollision", shell, "ball only: the kid's jumps, slides and rides stay the designed ones");
            StringAssert.Contains("ShapeChanged", shell, "again when the kid's collider changes shape for a slide");
        }
    }
}
