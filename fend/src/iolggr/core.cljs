(ns iolggr.core
  (:require-macros [cljs.core.async.macros :refer [go]])
  (:require [goog.dom :as gdom]
            [vega-tools.core :as vega-tools]
            [promesa.core :as p]
            [cljs.core.async :as async :refer [<! >! put! chan]]
            [clojure.string :as string]
  [om.next :as om :refer-macros [defui]]
            [om.dom :as dom])
  (:import [goog Uri]
           [goog.net Jsonp]))

(def initial-spec
  {:width  400
   :height 200
   :padding {:top 10, :left 30, :bottom 30, :right 10}

   :data
   [{:name "table"
     :values [{:x 1, :y 28} {:x 2, :y 55}
              {:x 3, :y 43} {:x 4, :y 91}
              {:x 5, :y 81} {:x 6, :y 53}
              {:x 7, :y 19} {:x 8, :y 87}
              {:x 9, :y 52} {:x 10, :y 48}
              {:x 11, :y 24} {:x 12, :y 49}
              {:x 13, :y 87} {:x 14, :y 66}
              {:x 15, :y 17} {:x 16, :y 27}
              {:x 17, :y 68} {:x 18, :y 16}
              {:x 19, :y 49} {:x 20, :y 15}]}]

   :scales
   [{:name "x"
     :type "ordinal"
     :range "width"
     :domain {:data "table", :field "x"}}
    {:name "y"
     :type "linear"
     :range "height"
     :domain {:data "table", :field "y"}, :nice true}]

   :axes
   [{:type "x", :scale "x"}
    {:type "y", :scale "y"}]

   :marks
   [{:type "rect", :from {:data "table"},
     :properties {:enter {:x {:scale "x", :field "x"}
                          :width {:scale "x", :band true, :offset -1}
                          :y {:scale "y", :field "y"}
                          :y2 {:scale "y", :value 0}}
                  :update {:fill {:value "steelblue"}}
                  :hover {:fill {:value "red"}}}}]})

(defui HelloWorld
  Object
  (render [this]
    (dom/div nil (get (om/props this) :title))))

(

   defui Chart
  Object
  (render [this]
    (dom/div nil "Hello, world!"))
  (
    componentDidMount [this]
                  (-> (vega-tools/validate-and-parse initial-spec)
                      (p/catch #(js/alert (str "Unable to parse spec:\n\n" %)))
                      (p/then #(-> (% {:el  (dom/node this)})
                                   (.update))))
                      )
  )






(def hello (om/factory Chart))

(js/ReactDOM.render
  ;; CHANGED
  (apply dom/div nil
         (map #(hello {:react-key %
                       :title (str "Hello " %)})
              (range 1)))
  (gdom/getElement "app"))

